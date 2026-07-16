"""
房源接口压力测试：对比 Redis 缓存开启 vs 关闭 的 QPS

原理:
  - 有缓存:  正常请求，预热后等 2s 再测试，缓存命中
  - 无缓存:  每个请求带 ?no_cache=1，后端显式跳过 Redis 读写

覆盖接口:
  轻量 ─ 单个房源  GET /houseinfo/<id>              (主键查, 1行)
  轻量 ─ 热门房源  GET /houseinfo/hotLists           (LIMIT 4)
  轻量 ─ 最新房源  GET /houseinfo/newLists           (LIMIT 4)
  重量 ─ 条件分页  GET /houseinfo/?page=1&per_page=10 (全表扫描+过滤+排序)

用法:
    python tests/stress_test_house.py

Windows 多 worker 启动 (必须先启服务再跑测试):
    pip install waitress
    waitress-serve --port=5000 --threads=8 app:app

    # 或者如果有 WSL:
    gunicorn -w 4 -k gevent app:app -b 0.0.0.0:5000

输出:
  - 控制台: 实时进度
  - 根目录: stress_test_report_<时间戳>.md
"""

import asyncio
import time
import statistics
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════
BASE_URL = "http://127.0.0.1:5000"
CONCURRENCY_LEVELS = [10, 50, 100, 200, 500, 1000, 2000]

REQUEST_MULTIPLIER = 3        # 每个并发平均处理的请求数
MIN_REQUESTS = 500            # 低并发时的保底请求数

def requests_for_level(concurrency: int) -> int:
    return max(concurrency * REQUEST_MULTIPLIER, MIN_REQUESTS)

OUTPUT_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

async def send_request(session: aiohttp.ClientSession, url: str) -> tuple[float, bool]:
    start = time.perf_counter()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            elapsed = time.perf_counter() - start
            success = 200 <= resp.status < 300
            await resp.read()
            return elapsed, success
    except Exception:
        return time.perf_counter() - start, False


async def run_burst(urls: list[str], concurrency: int) -> tuple[list[tuple[float, bool]], float]:
    connector = aiohttp.TCPConnector(limit=concurrency + 10, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded(url):
            async with semaphore:
                return await send_request(session, url)

        t0 = time.perf_counter()
        results = await asyncio.gather(*[bounded(u) for u in urls])
        wall_time = time.perf_counter() - t0
    return results, wall_time


async def warmup(url: str, times: int = 3):
    connector = aiohttp.TCPConnector(limit=5, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        for _ in range(times):
            try:
                async with session.get(url) as resp:
                    await resp.read()
            except Exception:
                pass
    # 等端口释放，防止 TIME_WAIT 耗尽影响后续 burst
    await asyncio.sleep(3)


def compute_stats(results: list[tuple[float, bool]], wall_time: float) -> dict:
    latencies = [r[0] for r in results if r[1]]
    errors = sum(1 for r in results if not r[1])
    total = len(results)
    if not latencies:
        return {"total": total, "errors": errors, "error_rate": 100.0,
                "qps": 0, "latency_avg": 0, "latency_min": 0, "latency_max": 0,
                "latency_p50": 0, "latency_p90": 0, "latency_p99": 0}
    latencies.sort()
    return {
        "total": total,
        "errors": errors,
        "error_rate": errors / total * 100,
        "qps": total / wall_time if wall_time > 0 else 0,
        "latency_avg": statistics.mean(latencies) * 1000,
        "latency_min": latencies[0] * 1000,
        "latency_max": latencies[-1] * 1000,
        "latency_p50": latencies[len(latencies) // 2] * 1000,
        "latency_p90": latencies[int(len(latencies) * 0.9)] * 1000,
        "latency_p99": latencies[int(len(latencies) * 0.99)] * 1000,
    }


# ═══════════════════════════════════════════════════════════════
# 测试场景
# ═══════════════════════════════════════════════════════════════

async def test_single_house(concurrency: int, count: int, house_id: int, no_cache: bool) -> dict:
    url = f"{BASE_URL}/houseinfo/{house_id}"
    if no_cache:
        url += "?no_cache=1"
    else:
        await warmup(url)
    urls = [url] * count
    results, wall_time = await run_burst(urls, concurrency)
    return compute_stats(results, wall_time)


async def test_list(concurrency: int, count: int, path: str, no_cache: bool) -> dict:
    url = f"{BASE_URL}{path}"
    if no_cache:
        url += "?no_cache=1"
    else:
        await warmup(url)
    urls = [url] * count
    results, wall_time = await run_burst(urls, concurrency)
    return compute_stats(results, wall_time)


QUERY_URL = f"{BASE_URL}/houseinfo/?page=1&per_page=10"

async def test_query(concurrency: int, count: int, no_cache: bool) -> dict:
    url = QUERY_URL
    if no_cache:
        url += "&no_cache=1"
    else:
        await warmup(url)
    urls = [url] * count
    results, wall_time = await run_burst(urls, concurrency)
    return compute_stats(results, wall_time)


# ═══════════════════════════════════════════════════════════════
# 控制台输出
# ═══════════════════════════════════════════════════════════════

def cprint(label: str, stats: dict):
    print(f"     {label:<8}  QPS={stats['qps']:>8.1f}  "
          f"avg={stats['latency_avg']:>7.1f}ms  "
          f"p99={stats['latency_p99']:>7.1f}ms  "
          f"err={stats['error_rate']:.1f}%")


# ═══════════════════════════════════════════════════════════════
# Markdown 报告生成
# ═══════════════════════════════════════════════════════════════

def _ratio_html(a: float, b: float, lower_is_better: bool = False) -> str:
    if b == 0:
        return "—"
    ratio = a / b
    if lower_is_better:
        color = "green" if ratio < 1 else ("red" if ratio > 1 else "")
    else:
        color = "green" if ratio > 1 else ("red" if ratio < 1 else "")
    if color:
        return f'<font color="{color}">{ratio:.1f}x</font>'
    return f"{ratio:.1f}x"


def _write_api_section(lines: list[str], title: str, endpoint: str, rows: list):
    """输出单个接口的 QPS / 延迟 / 错误率 三段表格"""
    lines.append(f"## {title}")
    lines.append(f"**接口**: {endpoint}  ")
    lines.append("")

    if not rows:
        lines.append("*(无数据)*")
        lines.append("")
        return

    # QPS
    lines.append("### QPS 对比")
    lines.append("")
    lines.append("| 并发数 | 请求数 | 有 Redis 缓存 | 无 Redis 缓存 | 缓存提升 |")
    lines.append("|--------|--------|--------------|--------------|---------|")
    for level, cached, uncached in rows:
        ratio_str = _ratio_html(cached["qps"], uncached["qps"], lower_is_better=False)
        lines.append(f"| {level} | {cached['total']} | {cached['qps']:>10.1f} req/s | "
                     f"{uncached['qps']:>10.1f} req/s | {ratio_str} |")
    lines.append("")

    # 延迟
    lines.append("### 延迟对比")
    lines.append("")
    lines.append("| 并发数 | 指标 | 有 Redis 缓存 | 无 Redis 缓存 | 降低 |")
    lines.append("|--------|------|--------------|--------------|------|")
    metrics = [("平均延迟", "latency_avg"), ("P50", "latency_p50"),
               ("P90", "latency_p90"), ("P99", "latency_p99")]
    for level, cached, uncached in rows:
        for i, (m_name, m_key) in enumerate(metrics):
            cv, uv = cached[m_key], uncached[m_key]
            ratio_str = _ratio_html(uv, cv, lower_is_better=True)
            level_str = str(level) if i == 0 else ""
            lines.append(f"| {level_str} | {m_name} | {cv:>7.1f} ms | {uv:>7.1f} ms | {ratio_str} |")
    lines.append("")

    # 错误率
    lines.append("### 错误率")
    lines.append("")
    lines.append("| 并发数 | 有 Redis 缓存 | 无 Redis 缓存 |")
    lines.append("|--------|--------------|--------------|")
    for level, cached, uncached in rows:
        lines.append(f"| {level} | {cached['error_rate']:.1f}% ({cached['errors']}/{cached['total']}) | "
                     f"{uncached['error_rate']:.1f}% ({uncached['errors']}/{uncached['total']}) |")
    lines.append("")
    lines.append("---")
    lines.append("")


def generate_markdown(all_results: dict, report_meta: dict) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"stress_test_report_{timestamp}.md"
    tpl = report_meta

    lines = []

    # 头部
    lines.append("# 房源系统 API 压力测试报告")
    lines.append("")
    lines.append(f"**测试时间**: {tpl['datetime']}  ")
    lines.append(f"**目标地址**: `{BASE_URL}`  ")
    lines.append(f"**服务器模式**: {tpl['server_mode']}  ")
    lines.append(f"**并发级别**: {CONCURRENCY_LEVELS}  ")
    lines.append(f"**请求数规则**: `max(并发 × {REQUEST_MULTIPLIER}, {MIN_REQUESTS})`  ")
    lines.append(f"**无缓存方式**: 后端 `?no_cache=1` 显式跳过 Redis  ")
    lines.append(f"**房源 ID**: {tpl['house_id']}  ")
    lines.append(f"**总耗时**: {tpl['duration']}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 轻量接口 ──
    lines.append("## 一、轻量接口")
    lines.append("")
    lines.append("> SQL 查询量小（主键查 / LIMIT 4），瓶颈在 Redis JSON 序列化 vs MySQL 简单查询。")
    lines.append("")

    _write_api_section(lines, "1. 单个房源", "`GET /houseinfo/<id>`",
                       all_results.get("single", []))

    _write_api_section(lines, "2. 热门房源", "`GET /houseinfo/hotLists`",
                       all_results.get("hot", []))

    _write_api_section(lines, "3. 最新房源", "`GET /houseinfo/newLists`",
                       all_results.get("new", []))

    # ── 重量接口 ──
    lines.append("## 二、重量接口")
    lines.append("")
    lines.append("> 全表扫描 + 多条件过滤 + 排序 + 分页，查询代价大，**Redis 缓存收益最明显**。")
    lines.append("")

    _write_api_section(lines, "4. 条件分页查询", "`GET /houseinfo/?page=1&per_page=10`",
                       all_results.get("query", []))

    # ── 总结 ──
    lines.append("## 总结")
    lines.append("")

    # 轻量
    lines.append("### 轻量接口")
    for key in ["single", "hot", "new"]:
        rows = all_results.get(key, [])
        if not rows:
            continue
        names = {"single": "单个房源", "hot": "热门房源", "new": "最新房源"}
        last_level, last_cached, last_uncached = rows[-1]
        qps_boost = last_cached["qps"] / last_uncached["qps"] if last_uncached["qps"] > 0 else 0
        lat_reduction = (last_uncached["latency_avg"] / last_cached["latency_avg"]
                         if last_cached["latency_avg"] > 0 else 0)
        lines.append(f"- **{names[key]}** ({last_level}并发): QPS 提升 **{qps_boost:.1f}x**，"
                     f"延迟降低 **{lat_reduction:.1f}x**")
    lines.append("")

    # 重量
    lines.append("### 重量接口")
    q_rows = all_results.get("query", [])
    if q_rows:
        last_level, last_cached, last_uncached = q_rows[-1]
        qps_boost = last_cached["qps"] / last_uncached["qps"] if last_uncached["qps"] > 0 else 0
        lat_reduction = (last_uncached["latency_avg"] / last_cached["latency_avg"]
                         if last_cached["latency_avg"] > 0 else 0)
        lines.append(f"- **条件分页查询** ({last_level}并发): QPS 提升 **{qps_boost:.1f}x**，"
                     f"延迟降低 **{lat_reduction:.1f}x**")
        lines.append("")
        lines.append("> 条件分页查询涉及全表扫描 + 过滤排序，MySQL 代价大，Redis 缓存收益显著。"
                     "面试中可重点展示这组对比数据。")
    lines.append("")

    lines.append("---")
    lines.append(f"*报告由 `tests/stress_test_house.py` 自动生成*")

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


# ═══════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════

async def probe_valid_id() -> int | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/houseinfo/?page=1&per_page=1",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
                items = data.get("data", {}).get("items", [])
                if items:
                    return items[0]["id"]
    except Exception:
        pass
    return None


async def main():
    start_time = datetime.now()

    print(f"\n{'═' * 60}")
    print("  房源系统 API 压力测试  ——  Redis 缓存 ON vs OFF")
    print(f"  目标: {BASE_URL}")
    print(f"  并发: {CONCURRENCY_LEVELS}")
    print(f"  输出: {OUTPUT_DIR}/stress_test_report_*.md")
    print(f"{'═' * 60}")

    # 连通性检查
    print("\n  检查后端连通性...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                text = await resp.text()
                print(f"  ✓ 后端连接成功 -> {text.strip()}")
    except Exception as e:
        print(f"  ✗ 无法连接后端: {e}")
        sys.exit(1)

    # 探测房源 ID
    target_id = await probe_valid_id()
    if target_id is None:
        print("  ✗ 未找到房源数据")
        sys.exit(1)
    print(f"  ✓ 使用房源 ID = {target_id}")

    # 推断服务器模式（仅用于报告标注）
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                server_header = resp.headers.get("Server", "")
                if "waitress" in server_header.lower():
                    server_mode = "waitress (多线程)"
                elif "gunicorn" in server_header.lower():
                    server_mode = "gunicorn (多 worker)"
                else:
                    server_mode = "Werkzeug (Flask dev server, 单线程)"
    except Exception:
        server_mode = "未知"

    # 逐接口测试
    all_results = {}

    for level in CONCURRENCY_LEVELS:
        total_req = requests_for_level(level)
        print(f"\n{'─' * 60}")
        print(f"  并发={level:<5}  请求={total_req}")
        print(f"{'─' * 60}")

        # 轻量: 单个房源
        print("  [轻] 单个房源")
        cached = await test_single_house(level, total_req, target_id, no_cache=False)
        cprint("有缓存", cached)
        await asyncio.sleep(1)
        uncached = await test_single_house(level, total_req, target_id, no_cache=True)
        cprint("无缓存", uncached)
        all_results.setdefault("single", []).append((level, cached, uncached))

        # 轻量: 热门
        print("  [轻] 热门房源")
        cached = await test_list(level, total_req, "/houseinfo/hotLists", no_cache=False)
        cprint("有缓存", cached)
        await asyncio.sleep(1)
        uncached = await test_list(level, total_req, "/houseinfo/hotLists", no_cache=True)
        cprint("无缓存", uncached)
        all_results.setdefault("hot", []).append((level, cached, uncached))

        # 轻量: 最新
        print("  [轻] 最新房源")
        cached = await test_list(level, total_req, "/houseinfo/newLists", no_cache=False)
        cprint("有缓存", cached)
        await asyncio.sleep(1)
        uncached = await test_list(level, total_req, "/houseinfo/newLists", no_cache=True)
        cprint("无缓存", uncached)
        all_results.setdefault("new", []).append((level, cached, uncached))

        # 重量: 条件分页
        print("  [重] 条件分页")
        cached = await test_query(level, total_req, no_cache=False)
        cprint("有缓存", cached)
        await asyncio.sleep(1)
        uncached = await test_query(level, total_req, no_cache=True)
        cprint("无缓存", uncached)
        all_results.setdefault("query", []).append((level, cached, uncached))

    # 生成 Markdown 报告
    end_time = datetime.now()
    report_meta = {
        "datetime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "house_id": target_id,
        "server_mode": server_mode,
        "duration": str(end_time - start_time).split(".")[0],
    }
    report_path = generate_markdown(all_results, report_meta)

    print(f"\n{'═' * 60}")
    print(f"  测试完成!  服务器模式: {server_mode}")
    print(f"  总耗时: {report_meta['duration']}")
    print(f"  报告: {report_path}")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
