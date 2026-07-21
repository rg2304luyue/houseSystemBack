/*
 Navicat Premium Data Transfer

 Source Server         : luyue
 Source Server Type    : MySQL
 Source Server Version : 80039 (8.0.39)
 Source Host           : localhost:3306
 Source Schema         : flaskhousesystem

 Target Server Type    : MySQL
 Target Server Version : 80039 (8.0.39)
 File Encoding         : 65001

 Date: 16/07/2026 16:05:39
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for appointment
-- ----------------------------
DROP TABLE IF EXISTS `appointment`;
CREATE TABLE `appointment`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `property` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `time` datetime NOT NULL COMMENT '预约时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 53 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of appointment
-- ----------------------------
INSERT INTO `appointment` VALUES (1, 'a', 'a', '2025-05-15 20:15:11');
INSERT INTO `appointment` VALUES (2, 'aaaa', '万科魅力之城武广新城', '2025-05-18 16:00:00');
INSERT INTO `appointment` VALUES (3, 'aaaa', '万科魅力之城武广新城', '2025-04-30 16:00:00');
INSERT INTO `appointment` VALUES (4, 'aaaa', '万科魅力之城武广新城', '2025-05-29 16:00:00');
INSERT INTO `appointment` VALUES (5, 'aaaa', '万科魅力之城武广新城', '2025-05-29 16:00:00');
INSERT INTO `appointment` VALUES (6, 'aaaa', '万科魅力之城武广新城', '2025-05-20 16:00:00');
INSERT INTO `appointment` VALUES (7, 'aaaa', '万科魅力之城武广新城', '2025-05-29 16:00:00');
INSERT INTO `appointment` VALUES (8, 'aaaa', '万科魅力之城武广新城', '2025-05-25 16:00:00');
INSERT INTO `appointment` VALUES (9, 'aaaa', '万科魅力之城武广新城', '2025-05-01 16:00:00');
INSERT INTO `appointment` VALUES (10, 'aaaa', '万科魅力之城武广新城', '2025-05-20 16:00:00');
INSERT INTO `appointment` VALUES (11, 'aaaa', '万科魅力之城武广新城', '2025-06-20 16:00:00');
INSERT INTO `appointment` VALUES (12, 'aaaa', '万科魅力之城武广新城', '2026-04-29 16:00:00');
INSERT INTO `appointment` VALUES (13, 'aaaa', '万科魅力之城武广新城', '2026-04-29 16:00:00');
INSERT INTO `appointment` VALUES (14, 'aaaa', '万科魅力之城武广新城', '2026-04-28 16:00:00');
INSERT INTO `appointment` VALUES (15, '19511053624', '整租·北辰中央公园(慧辰园) 2室2厅 南', '2026-04-28 16:00:00');
INSERT INTO `appointment` VALUES (16, '16608188855', '独栋·华佑e家 万国城店 无中介费可月付 润和珠江星环马厂地铁站 万国城两室 2室2厅', '2026-05-01 16:00:00');
INSERT INTO `appointment` VALUES (17, '19511053624', '整租·北辰中央公园(慧辰园) 2室2厅 南', '2026-05-02 16:00:00');
INSERT INTO `appointment` VALUES (18, '16608188855', '整租·北辰中央公园(慧辰园) 2室2厅 南', '2026-05-14 16:00:00');
INSERT INTO `appointment` VALUES (19, '19511053624', '整租·融城花苑 3室2厅 南', '2026-05-15 16:00:00');
INSERT INTO `appointment` VALUES (20, '19511053624', '整租·融城花苑 3室2厅 南', '2026-05-28 16:00:00');
INSERT INTO `appointment` VALUES (21, '16608188855', '整租·锦源小区 1室1厅 东西', '2026-05-30 16:00:00');
INSERT INTO `appointment` VALUES (22, 'autotest_appointment_user', '测试房源-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (23, 'autotest_appointment_user', '测试房源-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (24, 'autotest_appointment_user', '测试房源-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (25, 'autotest_appointment_user', '测试房源-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (26, 'autotest_appointment_user', '测试房源-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (27, 'appointment_test_user', '阳光花园-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (28, 'utc_test_user', '测试房源UTC', '2025-09-01 14:00:00');
INSERT INTO `appointment` VALUES (29, 'iso_test_user', 'ISO测试房源', '2025-10-15 09:30:00');
INSERT INTO `appointment` VALUES (30, 'past_test', '过去时间测试', '2020-01-01 10:00:00');
INSERT INTO `appointment` VALUES (31, 'future_test', '未来测试', '2099-12-31 23:59:59');
INSERT INTO `appointment` VALUES (32, 'appointment_test_user', '阳光花园-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (33, 'utc_test_user', '测试房源UTC', '2025-09-01 14:00:00');
INSERT INTO `appointment` VALUES (34, 'iso_test_user', 'ISO测试房源', '2025-10-15 09:30:00');
INSERT INTO `appointment` VALUES (35, 'past_test', '过去时间测试', '2020-01-01 10:00:00');
INSERT INTO `appointment` VALUES (36, 'future_test', '未来测试', '2099-12-31 23:59:59');
INSERT INTO `appointment` VALUES (37, 'appointment_test_user', '阳光花园-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (38, 'utc_test_user', '测试房源UTC', '2025-09-01 14:00:00');
INSERT INTO `appointment` VALUES (39, 'iso_test_user', 'ISO测试房源', '2025-10-15 09:30:00');
INSERT INTO `appointment` VALUES (40, 'past_test', '过去时间测试', '2020-01-01 10:00:00');
INSERT INTO `appointment` VALUES (41, 'future_test', '未来测试', '2099-12-31 23:59:59');
INSERT INTO `appointment` VALUES (42, 'appointment_test_user', '阳光花园-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (43, 'utc_test_user', '测试房源UTC', '2025-09-01 14:00:00');
INSERT INTO `appointment` VALUES (44, 'iso_test_user', 'ISO测试房源', '2025-10-15 09:30:00');
INSERT INTO `appointment` VALUES (45, 'past_test', '过去时间测试', '2020-01-01 10:00:00');
INSERT INTO `appointment` VALUES (46, 'future_test', '未来测试', '2099-12-31 23:59:59');
INSERT INTO `appointment` VALUES (47, 'appointment_test_user', '阳光花园-1栋101', '2025-08-01 10:00:00');
INSERT INTO `appointment` VALUES (48, 'utc_test_user', '测试房源UTC', '2025-09-01 14:00:00');
INSERT INTO `appointment` VALUES (49, 'iso_test_user', 'ISO测试房源', '2025-10-15 09:30:00');
INSERT INTO `appointment` VALUES (50, 'past_test', '过去时间测试', '2020-01-01 10:00:00');
INSERT INTO `appointment` VALUES (51, 'future_test', '未来测试', '2099-12-31 23:59:59');
INSERT INTO `appointment` VALUES (52, '16608188855', '整租·楚天世纪城 3室2厅 南', '2026-05-15 16:00:00');

-- ----------------------------
-- Table structure for channel
-- ----------------------------
DROP TABLE IF EXISTS `channel`;
CREATE TABLE `channel`  (
  `channel_id` int NOT NULL AUTO_INCREMENT,
  `tenant_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '租客用户名',
  `landlord_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '房东用户名',
  `timestamp` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`channel_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of channel
-- ----------------------------
INSERT INTO `channel` VALUES (1, 'Andy', 'Lu', '2025-05-21 19:25:54');
INSERT INTO `channel` VALUES (2, 'Ylfmoonn', '赵先生', '2025-06-02 14:32:18');
INSERT INTO `channel` VALUES (3, 'Lappand', 'Ylfmoonn', '2025-06-07 22:42:01');
INSERT INTO `channel` VALUES (4, 'aaaa', '房东', '2025-06-12 19:31:50');
INSERT INTO `channel` VALUES (5, 'aaaa', '华佑e家', '2025-06-12 19:32:12');
INSERT INTO `channel` VALUES (6, 'Lappand', 'luyue', '2026-04-30 15:01:57');
INSERT INTO `channel` VALUES (7, 'Lappand', '赵先生', '2026-05-08 15:22:11');
INSERT INTO `channel` VALUES (8, '张先生', 'luyue', '2026-05-09 15:50:33');
INSERT INTO `channel` VALUES (9, 'auto_test_user', 'test_receiver', '2026-05-11 15:42:16');
INSERT INTO `channel` VALUES (10, '房东', 'luyue', '2026-05-13 17:05:41');

-- ----------------------------
-- Table structure for chat_message
-- ----------------------------
DROP TABLE IF EXISTS `chat_message`;
CREATE TABLE `chat_message`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL COMMENT '关联 chat_session 表的 id',
  `role` enum('user','assistant') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '发送者角色',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '消息文本内容',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_message_session`(`session_id` ASC) USING BTREE,
  CONSTRAINT `fk_message_session` FOREIGN KEY (`session_id`) REFERENCES `chat_session` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 77 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chat_message
-- ----------------------------
INSERT INTO `chat_message` VALUES (1, 1, 'user', '你好，请问你能推荐一些岳麓区的房源吗', '2026-04-28 14:27:01');
INSERT INTO `chat_message` VALUES (2, 1, 'assistant', '很抱歉，目前在岳麓区暂时没有匹配的房源。建议您可以适当放宽一些条件，比如：\n\n- 扩大区域范围（例如包含临近的高新区或望城区）\n- 调整预算区间（提高或降低租金预期）\n- 不限制是否近地铁\n- 接受不同户型（如一居室、开间、合租等）\n\n如果您能提供更具体的需求（比如预算范围、期望户型、是否必须近地铁等），我可以帮您更精准地查找！', '2026-04-28 14:27:11');
INSERT INTO `chat_message` VALUES (3, 1, 'user', '你能推荐一些最高2000元以下的房源吗', '2026-04-28 14:27:52');
INSERT INTO `chat_message` VALUES (4, 1, 'assistant', '太好了！在 **2000元以下** 的预算范围内，我为您找到了几套高性价比的房源，其中**有一套就在岳麓区**，非常适合您！\n\n### 🌟 岳麓区推荐（预算内）\n- **房源名称**：合租·保利麓谷林语D区 4居室 南卧  \n- **区域**：岳麓区 · 麓谷西  \n- **价格**：仅 **799元/月**  \n- **面积**：28㎡，朝南，采光好  \n- **配置**：精装、近地铁、可立即入住  \n- **房东**：美美公寓（专业托管，服务有保障）\n\n这套房子位于岳麓区热门板块“麓谷”，周边产业聚集、交通便利，且是精装修南向卧室，性价比非常高！\n\n---\n\n### 💡 其他高性价比备选（芙蓉区 & 雨花区）\n如果您也愿意考虑临近区域，这些房源同样优质：\n\n1. **运通尊苑（芙蓉区）**  \n   - 499元/月 | 22㎡南卧 | 精装合租 | 近地铁  \n2. **长远华樟名府（雨花区）**  \n   - 540元/月 | 25㎡南卧 | 精装合租 | 新上架房源  \n3. **泰时新雅园（芙蓉区）**  \n   - 580元/月 | 18㎡南卧 | 精装合租 | 浏览量超900次，人气极高！\n\n---\n\n需要我帮您查看某套房源的**详细信息**（如户型图、具体地址、室友情况等）吗？或者您希望我再按其他条件（比如只看岳麓区、必须独立卫生间等）进一步筛选？欢迎随时告诉我！ 😊', '2026-04-28 14:28:09');
INSERT INTO `chat_message` VALUES (5, 2, 'user', '你能推荐一些靠近地铁的房源吗', '2026-04-28 14:29:25');
INSERT INTO `chat_message` VALUES (6, 2, 'assistant', '太好了！我为您筛选出几套**靠近地铁**的优质房源，覆盖不同区域和预算，既有整租也有合租选择，方便您根据需求灵活挑选：\n\n---\n\n### 🏠 **1. 桃花村·2室1厅整租（岳麓区）**\n- **价格**：仅 ¥1000/月  \n- **面积**：62㎡｜南北通透｜简装  \n- **亮点**：整租性价比极高，适合情侣或小家庭；位于岳麓区桃花村，生活便利，且明确标注近地铁。  \n- **房东**：张先生（电话：13630278915）\n\n---\n\n### 🛏️ **2. 冠寓长沙大王山店·精装单间（品牌公寓）**\n- **价格**：¥1082/月（首月特惠）  \n- **面积**：25㎡｜精装｜拎包入住  \n- **亮点**：品牌长租公寓，无中介、押一付一，学生优惠；紧邻地铁，安全私密性好，适合上班族或学生党。  \n- **运营方**：冠寓（电话：15012340002）\n\n---\n\n### 👥 **3. 博林金谷·南向合租主卧（天心区新开铺）**\n- **价格**：¥1150/月  \n- **面积**：28㎡｜精装｜4居室中的南卧  \n- **亮点**：位于天心区成熟社区“博林金谷”，精装合租，采光好；近地铁，交通便捷，适合预算有限但追求品质的年轻人。  \n- **公寓品牌**：快聚租公寓（电话：18612340024）\n\n---\n\n### 🌆 **4. 尚鑫海悦·小户型整租（长沙县开元路）**\n- **价格**：¥1200/月  \n- **面积**：28㎡｜简装｜1室0厅  \n- **亮点**：独立整租，私密性强；虽在长沙县，但靠近地铁，通勤方便，适合单身人士过渡居住。  \n- **房东**：丁先生（电话：15612340015）\n\n---\n\n### 🚇 **5. 湘江悦家·麓隐桐溪店·地铁口开间（大王山）**\n- **价格**：¥1220/月（开业95折）  \n- **面积**：37.28㎡｜精装｜1室0厅1卫  \n- **亮点**：**正对3号线大王山地铁口**！品牌公寓，无中介费、无服务费，精装交付，适合注重通勤效率的租客。  \n- **运营方**：湘江悦家（电话：19012340028）\n\n---\n\n如果您对其中某一套特别感兴趣，我可以帮您获取更详细的房源信息（如户型图、周边配套等）。或者，如果您有更具体的预算、区域或户型偏好，也可以告诉我，我会进一步精准推荐！', '2026-04-28 14:29:53');
INSERT INTO `chat_message` VALUES (21, 10, 'user', '你好，请问今天天气如何，能推荐一些在雨花区，2000元以下的房子吗', '2026-04-29 20:08:42');
INSERT INTO `chat_message` VALUES (22, 10, 'assistant', '太好了！今天长沙天气非常适宜看房哦！\n\n🌤️ **今日天气**：多云，16°C，微风≤3级，湿度73%  \n📅 **最佳看房日**：建议选择明天（4月30日），多云24°C，舒适宜人！\n\n---\n\n为您精选了**雨花区2000元以下的优质房源**，既有整租也有合租选择：\n\n### 🏠 **【合租优选】长远华樟名府·南卧**\n- 📍 区域：雨花·尚东 | 面积：25㎡ | 户型：5室1厅3卫（合租单间）\n- 💰 租金：**540元/月**（超值！）\n- ✨ 亮点：精装、近地铁、朝南采光好，全新上架！\n\n### 🏠 **【整租精品】2076至高点·1室1厅**\n- 📍 区域：雨花·左家塘 | 面积：41㎡ | 户型：1室1厅\n- 💰 租金：**1100元/月**\n- ✨ 亮点：精装交付，独立一居室，私密性好\n\n### 🏠 **【高性价比整租】融城花苑·3室2厅**\n- 📍 区域：雨花·井湾子 | 面积：99㎡ | 户型：3室2厅\n- 💰 租金：**1300元/月**\n- ✨ 亮点：近100㎡大三房，精装，适合家庭或多人合租\n\n### 🏠 **【地铁房推荐】锦源小区·2室1厅**\n- 📍 区域：雨花·树木岭 | 面积：73㎡ | 户型：2室1厅1卫\n- 💰 租金：**1600元/月**\n- ✨ 亮点：**近地铁**、朝南、精装，交通便利！\n\n### 🏠 **【实惠之选】九龙小区·2室1厅**\n- 📍 区域：雨花·树木岭 | 面积：73㎡ | 户型：2室1厅1卫\n- 💰 租金：**1800元/月**\n- ✨ 亮点：近地铁、精装，树木岭成熟生活圈\n\n---\n\n需要我帮您详细了解某一套房源的具体信息（如照片、楼层、家电配置等），或者安排看房时间吗？也可以为您查询这些小区周边的配套（超市、学校、医院等）哦！', '2026-04-29 20:09:06');
INSERT INTO `chat_message` VALUES (23, 11, 'user', '你能推荐一些芙蓉区的3000元以下的房源吗', '2026-04-29 21:12:48');
INSERT INTO `chat_message` VALUES (24, 11, 'assistant', '当然可以！在芙蓉区3000元以下的预算范围内，我为您精选了几套高性价比的房源，既有合租也有整租选择，全部价格远低于您的预算上限：\n\n---\n\n🏠 **合租·运通尊苑 5居室 南卧**  \n📍 区域：芙蓉区马王堆 | 面积：22㎡ | 户型：5室1厅2卫（合租南卧）  \n💰 租金：**499元/月**  \n✨ 亮点：精装交付、近地铁、朝南采光好，由长沙鸿威公寓管理，安全有保障！\n\n🏠 **合租·泰时新雅园 4居室 南卧**  \n📍 区域：芙蓉区晚报片区 | 面积：18㎡ | 户型：4室2厅2卫（合租南卧）  \n💰 租金：**580元/月**  \n✨ 亮点：精装房、近地铁，页面浏览量高达900+，非常抢手！房东为知名“龟壳公寓”，服务规范。\n\n🏠 **合租·东方新城 5居室 南卧**  \n📍 区域：芙蓉区德政园 | 面积：18㎡ | 户型：5居室（合租南卧）  \n💰 租金：**599元/月**  \n✨ 亮点：近地铁，虽然为毛坯装修，但价格极具优势，适合预算敏感型租客。\n\n🏠 **整租·锦源小区 1室1厅（实际为2室1厅）**  \n📍 区域：芙蓉区树木岭 | 面积：50㎡ | 户型：2室1厅1卫（整租）  \n💰 租金：**800元/月**  \n✨ 亮点：整租仅800元！近地铁，简装实用，适合情侣或小家庭，性价比极高！\n\n🏠 **合租·山水华景 5居室 南卧**  \n📍 区域：芙蓉区马王堆 | 面积：25㎡ | 户型：5室1厅2卫（合租南卧）  \n💰 租金：**849元/月**  \n✨ 亮点：面积更大（25㎡），精装南向卧室，居住舒适度高。\n\n---\n\n所有房源均在**3000元以内**，最低仅**499元/月**！如果您对其中某一套感兴趣，我可以帮您获取更详细的房源信息（如实景照片、具体楼层、水电费用等），或者安排看房。也可以根据您的通勤地点（比如是否靠近五一广场、火车站等）进一步筛选。\n\n需要我帮您深入了解哪一套？或者您更倾向整租还是合租？', '2026-04-29 21:13:10');
INSERT INTO `chat_message` VALUES (25, 1, 'user', '你能推荐一些有空调，靠近地铁的房源吗，你觉得今天适合看房吗', '2026-04-30 10:00:02');
INSERT INTO `chat_message` VALUES (26, 1, 'assistant', '非常感谢您的耐心！关于您的需求——**2000元以内、带空调、靠近地铁的房源**，我刚刚进行了精准查询，但目前系统中**暂无完全匹配“带空调+近地铁”且在2000元以下的房源**。\n\n不过别担心！我可以给您两个实用建议：\n\n---\n\n### 🔍 建议一：适当放宽条件，快速找到理想房\n您可以考虑以下调整方式：\n- **优先保证“近地铁”**，空调可协商（很多房东可临时加装或提供风扇）\n- **或优先“带空调”**，地铁步行稍远（比如10-15分钟内也算便利）\n- **扩大区域选择**：目前平台在 **雨花、芙蓉、天心、岳麓、望城、长沙县** 都有活跃房源\n\n例如，如果您愿意先看看 **岳麓区近地铁的房源**（空调可后续确认），我可以立刻为您筛选！\n\n---\n\n### ☀️ 关于今天是否适合看房？\n**非常适合！**  \n根据长沙今日天气预报：\n- **当前天气**：晴天，19°C，微风，湿度舒适\n- **今日白天**：多云，最高23°C，东风1-3级\n- **看房建议**：✅ **今天是绝佳看房日！** 光线充足，能真实感受房间采光和通风。建议 **上午10点至下午4点** 之间看房，效果最佳！\n\n> ⚠️ 注意：明天（5月1日）也还不错，但**5月2日有中雨**，不建议安排看房。\n\n---\n\n### 📌 下一步行动建议\n请告诉我您更看重哪一点？我可以立即为您重新筛选：\n1. **必须近地铁** → 我找地铁500米内房源（空调另确认）\n2. **必须带空调** → 我优先筛选明确标注有空调的房子\n3. **指定区域** → 比如只看岳麓区 or 雨花区？\n\n只需一句话，我马上为您定制推荐！ 😊', '2026-04-30 10:00:33');
INSERT INTO `chat_message` VALUES (27, 10, 'user', '你好，请问今天天气如何，能推荐一些在岳麓区，有空调的房子吗', '2026-04-30 17:50:47');
INSERT INTO `chat_message` VALUES (28, 10, 'assistant', '🌤️ **今日岳麓区天气**：晴天，23°C，微风≤3级，湿度39%  \n📅 **最佳看房时间**：今天（4月30日）就是绝佳时机！建议上午10点到下午4点之间去看房，采光效果一目了然！\n\n---\n\n关于您提到的“岳麓区有空调的房子”，我刚刚查询了房源数据库，**暂时没有直接标注“空调”作为筛选条件的房源**。不过，在长沙租房市场中，**绝大多数精装或简装房源都已配备空调**，尤其是近2年上架的房源。\n\n为了更精准地为您推荐，我可以按以下方式优化搜索：\n- 按预算范围（如2000元以内/3000元以内）\n- 按户型（如1室1厅、2室1厅等）\n- 是否需要近地铁\n- 是否接受合租或仅整租\n\n或者，我也可以先为您推荐几套**岳麓区热门且大概率带空调的精装房源**，您看是否需要？\n\n另外，如果您对空调品牌、数量（如每个房间都有）有特别要求，也可以告诉我，我会在后续详细介绍房源时重点确认这一点！\n\n您希望怎么继续？🙂', '2026-04-30 17:51:04');
INSERT INTO `chat_message` VALUES (29, 12, 'user', '你好，你能推荐一些在芙蓉区的，3000元以下的房源吗', '2026-05-02 14:57:30');
INSERT INTO `chat_message` VALUES (30, 12, 'assistant', '太好了！我在芙蓉区为您找到了几套3000元以下的优质房源，既有合租房也有整租房源，价格都非常实惠。以下是精选推荐：\n\n🏠 **合租·运通尊苑 5居室 南卧**  \n📍 区域：芙蓉区马王堆 | 面积：22㎡ | 户型：5室1厅2卫（合租单间）  \n💰 租金：499元/月  \n✨ 亮点：精装交付、朝南卧室、近地铁，性价比极高！\n\n🏠 **合租·泰时新雅园 4居室 南卧**  \n📍 区域：芙蓉区晚报片区 | 面积：18㎡ | 户型：4室2厅2卫（合租单间）  \n💰 租金：580元/月  \n✨ 亮点：精装房、朝南采光好、近地铁，人气较高（已超900次浏览）\n\n🏠 **合租·东方新城 5居室 南卧**  \n📍 区域：芙蓉区德政园 | 面积：18㎡ | 户型：5居室（合租单间）  \n💰 租金：599元/月  \n✨ 亮点：近地铁，适合预算有限但希望交通便利的朋友\n\n🏠 **整租·锦源小区 1室1厅**  \n📍 区域：芙蓉区树木岭 | 面积：50㎡ | 户型：2室1厅1卫（整租）  \n💰 租金：800元/月  \n✨ 亮点：可整租、简装实用、近地铁，适合小家庭或情侣居住\n\n> 💡 温馨提示：以上房源租金远低于您3000元的预算上限，选择空间非常大！如果您对某一套感兴趣，我可以帮您获取更详细的房源信息，或者安排看房。\n\n请问您更倾向于合租还是整租？或者需要我根据其他条件（如具体地铁线路、装修要求等）进一步筛选吗？', '2026-05-02 14:57:48');
INSERT INTO `chat_message` VALUES (31, 1, 'user', '今天适合看房吗？', '2026-05-08 15:33:03');
INSERT INTO `chat_message` VALUES (32, 1, 'assistant', '今天（5月8日）长沙是**小雨天气**，气温18°C，湿度较高（79%），风力4级。\n\n🌧️ **是否适合看房？**  \n✅ **其实非常适合！** 虽然下雨，但**雨天正是检验房子防水、隔音和排水性能的黄金时机**！您可以重点观察：\n- 天花板、墙面是否有渗水或发霉痕迹\n- 窗户密封性好不好（是否漏雨）\n- 楼道、电梯间是否积水\n\n📌 **看房小贴士**：\n- 建议携带伞和防滑鞋\n- 优先选择白天（10:00–16:00）看房，光线相对充足\n- 可顺便测试室内通风除湿效果\n\n🌤️ **未来三天天气参考**：\n- **5月9日**：阴转多云，16~24°C，更舒适\n- **5月10日**：阴天，19~27°C，气温回升\n\n> 如果您不介意小雨，**今天看房反而能发现平时看不到的问题**，是理性租房的好机会！需要我帮您预约一套近地铁的房源实地查看吗？', '2026-05-08 15:33:17');
INSERT INTO `chat_message` VALUES (33, 1, 'user', '那你能推荐一些有洗衣机的房源吗？', '2026-05-08 17:00:21');
INSERT INTO `chat_message` VALUES (34, 1, 'assistant', '太好了！在 **2000元以内** 的预算下，我为您找到了 **5套配备洗衣机、且靠近地铁的优质合租房源**，其中**1套就在岳麓区**，非常适合您！\n\n---\n\n### 🏠 **重点推荐：岳麓区 · 保利麓谷林语D区**\n- **价格**：799元/月  \n- **面积**：28㎡ 南卧（朝南采光好）  \n- **配置**：✅ 精装修 + ✅ 洗衣机 + ✅ 近地铁 + ✅ 可立即入住  \n- **房东**：美美公寓（专业托管，服务可靠）  \n- **人气**：近期浏览量达456次，新上架房源！\n\n> 这是目前**岳麓区唯一一套符合“带洗衣机+近地铁+2000元内”条件的房源**，性价比极高！\n\n---\n\n### 💰 其他高性价比选择（芙蓉区 & 雨花区）\n\n1. **运通尊苑（芙蓉·马王堆）**  \n   - 499元/月 | 22㎡南卧 | 精装合租 | 近地铁 | 配洗衣机  \n   - 房东：长沙鸿威公寓\n\n2. **长远华樟名府（雨花·尚东）**  \n   - 540元/月 | 25㎡南卧 | 精装合租 | 近地铁 | 新上架+配洗衣机  \n   - 浏览量61次，热度上升中！\n\n3. **泰时新雅园（芙蓉·晚报）**  \n   - 580元/月 | 18㎡南卧 | 精装合租 | 近地铁 | 配洗衣机  \n   - **超人气房源！浏览量高达903次**，口碑极佳！\n\n4. **东方新城（芙蓉·德政园）**  \n   - 599元/月 | 18㎡南卧 | 近地铁 | 配洗衣机  \n   - 注：为毛坯装修，但功能齐全，适合预算优先的租客\n\n---\n\n### 📌 下一步建议\n- 如果您对**岳麓区这套799元的房源**感兴趣，我可以立即为您调取**详细信息**（如户型图、室友情况、具体地铁距离等）。\n- 或者，您也可以告诉我是否希望**只看岳麓区**，或是否接受**稍高一点的预算**（比如2500元），我可以进一步优化推荐！\n\n今天小雨天气正适合实地检验房屋质量，需要帮您预约看房吗？😊', '2026-05-08 17:00:45');
INSERT INTO `chat_message` VALUES (35, 13, 'user', '你好，请问今天天气适合看房吗', '2026-05-09 16:13:41');
INSERT INTO `chat_message` VALUES (36, 13, 'assistant', '今天长沙天气非常适宜看房！🌤️\n\n当前是**多云天气，气温24°C**，风力≤3级，湿度适中（61%），体感舒适，不会太晒也不会闷热，正是实地看房的好时机！\n\n未来三天也都是**多云为主**，气温逐渐回升：\n- **5月10日（明天）**：28°C / 18°C，多云，微风 —— 被系统推荐为**最佳看房日**！\n- **5月11日**：30°C / 21°C，同样多云，适合白天看房。\n\n💡 **看房小建议**：  \n由于是多云天气，室内采光效果会比较真实，建议您重点观察房间的**自然光照是否充足**、是否有暗角，这对日后居住体验影响很大。\n\n如果您有心仪区域或房源，我可以帮您安排推荐或查询周边配套！需要吗？😊', '2026-05-09 16:13:53');
INSERT INTO `chat_message` VALUES (37, 14, 'user', '帮我推荐一个两居室的房子', '2026-05-11 15:42:07');
INSERT INTO `chat_message` VALUES (38, 14, 'assistant', '您好！很高兴为您推荐两居室的房子。为了给您提供更精准的房源推荐，我需要了解一些基本信息：\n\n1. **预算范围**：您每月能接受的租金大概是多少？\n2. **区域偏好**：您希望在长沙哪个区租房？（比如岳麓、天心、雨花、开福等）\n3. **交通需求**：是否需要靠近地铁站？\n4. **其他要求**：比如装修情况、楼层、小区环境等\n\n如果您暂时没有明确的区域或预算，我可以先为您展示当前平台上最受欢迎的两居室房源作为参考。请问您希望哪种方式呢？', '2026-05-11 15:42:12');
INSERT INTO `chat_message` VALUES (39, 15, 'user', '帮我推荐一个两居室的房子', '2026-05-11 15:43:25');
INSERT INTO `chat_message` VALUES (40, 15, 'assistant', '太好了！我为您筛选出当前**最受欢迎的两居室房源**，其中正好有几套非常优质的2室户型，性价比高、配套齐全。以下是重点推荐：\n\n---\n\n### 🏠 **1. 包租婆宿懒公寓 · 保利天禧**\n- 📍 **区域**：近六沟垅地铁（岳麓区核心地段）\n- 📐 **面积**：38㎡ | **户型**：2室1厅\n- 💰 **租金**：2750元/月（可月付，无中介费！）\n- ✨ **亮点**：\n  - 精装修，一线江景视野\n  - 步行可达**六沟垅地铁站**、**山姆超市**、**万象城**\n  - 支持月付，灵活方便，适合年轻人或小家庭\n\n---\n\n### 🏠 **2. 北辰中央公园（慧辰园） · 天心区政府旁**\n- 📍 **区域**：天心区省政府板块\n- 📐 **面积**：95㎡ | **户型**：2室2厅（南北通透，朝南）\n- 💰 **租金**：3000元/月\n- ✨ **亮点**：\n  - 精装大两居，空间宽敞舒适\n  - 位于政务核心区，环境安静，生活便利\n  - 小区品质高，物业管理完善\n\n---\n\n### 🏠 **3. 华佑e家 · 万国城店（近马厂地铁）**\n- 📍 **区域**：开福区万国城（近马厂地铁站）\n- 📐 **面积**：76㎡ | **户型**：2室2厅\n- 💰 **租金**：2208元/月（超高性价比！）\n- ✨ **亮点**：\n  - 精装修，拎包入住\n  - 紧邻**马厂地铁站**，通勤便捷\n  - 无中介费，支持月付，经济实惠\n\n---\n\n这三套都是近期浏览量很高的热门房源，各有特色：\n- 如果您看重**交通便利和商圈配套**，推荐**保利天禧**；\n- 如果偏好**大空间和安静环境**，**北辰中央公园**很合适；\n- 如果预算有限又想要**地铁+精装**，**万国城这套2208元**非常划算！\n\n请问您对哪一套更感兴趣？我可以为您调取详细信息（如实拍图、具体楼层、周边学校/医院等），或者根据您的具体预算和区域再做精准筛选！', '2026-05-11 15:43:48');
INSERT INTO `chat_message` VALUES (41, 16, 'user', '帮我推荐一个两居室的房子', '2026-05-11 15:48:25');
INSERT INTO `chat_message` VALUES (42, 16, 'assistant', '您好！很高兴为您推荐两居室的房子。为了更精准地匹配您的需求，我需要了解一些关键信息：\n\n1. **预算范围**：您每月能接受的租金大概是多少？（例如：2000-3000元）\n2. **区域偏好**：您希望在长沙哪个区租房？（如岳麓、天心、雨花、开福等）\n3. **交通要求**：是否需要靠近地铁站？\n4. **其他要求**：比如装修情况（精装/简装）、小区环境等。\n\n如果您暂时没有明确要求，我可以先为您展示当前平台上**最受欢迎的5套两居室房源**作为参考！请问您希望哪种方式？', '2026-05-11 15:48:31');
INSERT INTO `chat_message` VALUES (43, 17, 'user', '帮我推荐一个两居室的房子', '2026-05-11 15:49:43');
INSERT INTO `chat_message` VALUES (44, 17, 'assistant', '太好了！我在热门房源中为您筛选出了几套高人气的**两居室**（2室1厅或2室2厅）房子，都是当前租客关注度很高的优质房源：\n\n---\n\n🏠 **【包租婆宿懒公寓 · 保利天禧】**  \n📍 区域：近六沟垅地铁（岳麓区核心地段）  \n📐 面积：38㎡ | 户型：2室1厅  \n💰 租金：2750元/月  \n✨ 亮点：**精装交付、一线江景、近地铁、山姆超市&万象城环绕、支持月付、无中介费**！虽然面积不算大，但布局合理，适合小家庭或情侣。\n\n---\n\n🏠 **【北辰中央公园（慧辰园）· 天心省政府板块】**  \n📍 区域：天心区 · 省政府板块  \n📐 面积：95㎡ | 户型：2室2厅 | 朝南  \n💰 租金：3000元/月  \n✨ 亮点：**精装大两居、全屋朝南采光好、小区品质高、环境安静**，适合追求居住舒适度的您！\n\n---\n\n🏠 **【华佑e家 · 万国城店】**  \n📍 区域：近马厂地铁站（开福区）  \n📐 面积：76㎡ | 户型：2室2厅  \n💰 租金：2208元/月  \n✨ 亮点：**性价比超高！精装、近地铁、无中介费、可月付**，楚天世纪城社区成熟，生活便利。\n\n---\n\n这几套都是目前平台上的“爆款”两居室，各有特色：\n- 如果您看重**地段和配套**，推荐 **保利天禧**；\n- 如果您偏好**宽敞明亮的大户型**，**北辰中央公园**非常合适；\n- 如果预算有限又想**近地铁+低门槛入住**，**万国城这套2208元/月**很划算！\n\n请问您对哪一套更感兴趣？或者可以告诉我您的具体预算和区域偏好，我可以为您进一步精准筛选！也可以帮您查询周边配套、通勤时间等信息哦 😊', '2026-05-11 15:50:04');
INSERT INTO `chat_message` VALUES (45, 18, 'user', '帮我推荐一个两居室的房子', '2026-05-11 15:51:35');
INSERT INTO `chat_message` VALUES (46, 18, 'assistant', '您好！很高兴为您推荐两居室的房子。为了更精准地匹配您的需求，我需要了解一些关键信息：\n\n1. **预算范围**：您每月能接受的租金大概是多少？（例如：2000-3000元）\n2. **区域偏好**：您希望在长沙哪个区租房？（如岳麓、天心、雨花、开福等）\n3. **交通要求**：是否需要靠近地铁站？\n4. **其他需求**：比如装修情况（精装/简装）、小区环境等\n\n如果您暂时没有明确要求，我可以先为您展示当前平台上**最受欢迎的5套两居室房源**作为参考！您看哪种方式更适合您？', '2026-05-11 15:51:40');
INSERT INTO `chat_message` VALUES (47, 19, 'user', '帮我推荐一个两居室的房子', '2026-05-11 16:12:41');
INSERT INTO `chat_message` VALUES (48, 19, 'assistant', '您好！很高兴为您推荐两居室的房子。为了更精准地匹配您的需求，我需要了解一些基本信息：\n\n1. **预算范围**：您每月能接受的租金是多少？（例如：2000-3000元）\n2. **区域偏好**：您希望在长沙哪个区租房？（如岳麓、天心、雨花、开福等）\n3. **交通要求**：是否需要靠近地铁站？\n4. **其他要求**：比如装修情况（精装/简装）、楼层、小区环境等\n\n如果您暂时没有明确想法，我可以先为您展示当前平台上最受欢迎的几套两居室房源作为参考！', '2026-05-11 16:12:48');
INSERT INTO `chat_message` VALUES (50, 20, 'user', '帮我推荐一个两居室的房子', '2026-05-11 16:15:11');
INSERT INTO `chat_message` VALUES (51, 20, 'assistant', '您好！很高兴为您推荐两居室的房子。为了更精准地匹配您的需求，我需要了解一些基本信息：\n\n1. **预算范围**：您每月能接受的租金大概是多少？\n2. **区域偏好**：您希望在长沙哪个区租房？（比如岳麓、天心、雨花、开福等）\n3. **交通要求**：是否需要靠近地铁站？\n4. **其他要求**：比如装修情况（精装/简装）、楼层、小区环境等\n\n如果您暂时没有明确想法，我可以先为您展示当前平台上**最受欢迎的5套两居室房源**作为参考！您看可以吗？', '2026-05-11 16:15:16');
INSERT INTO `chat_message` VALUES (53, 21, 'user', '帮我推荐一个两居室的房子', '2026-05-11 16:16:45');
INSERT INTO `chat_message` VALUES (54, 21, 'assistant', '您好！很高兴为您推荐两居室的房子。为了更精准地匹配您的需求，我需要了解一些基本信息：\n\n1. **预算范围**：您每月能接受的租金大概是多少？\n2. **区域偏好**：有特别想住的区域吗？（比如岳麓、天心、雨花、开福等）\n3. **交通要求**：是否需要靠近地铁站？\n4. **其他要求**：比如装修情况、楼层、小区环境等\n\n如果您暂时没有明确要求，我可以先为您推荐几套当前平台上热门的两居室房源供参考！请问您希望哪种方式呢？', '2026-05-11 16:16:50');
INSERT INTO `chat_message` VALUES (56, 22, 'user', '帮我推荐一个两居室的房子', '2026-05-11 16:18:37');
INSERT INTO `chat_message` VALUES (57, 22, 'assistant', '太好了！我在热门房源中为您筛选出了 **3套高人气的两居室**，都是近期浏览量很高的优质房源，信息如下：\n\n---\n\n🏠 **【包租婆宿懒公寓 · 保利天禧】**  \n📍 区域：近六沟垅地铁（岳麓区）｜面积：38㎡｜户型：2室1厅  \n💰 租金：**2750元/月**  \n✨ 亮点：**精装交付、近地铁、一线江景、山姆超市 & 万象城环绕、支持月付、无中介费**！虽然面积不算大，但布局紧凑，适合小家庭或情侣。\n\n---\n\n🏠 **【北辰中央公园(慧辰园)】**  \n📍 区域：天心区省政府板块｜面积：95㎡｜户型：2室2厅（朝南）  \n💰 租金：**3000元/月**  \n✨ 亮点：**95㎡宽敞两居、精装、朝南采光好**，位于成熟社区北辰中央公园，生活配套齐全，适合追求居住舒适度的您。\n\n---\n\n🏠 **【华佑e家 · 万国城店】**  \n📍 区域：近马厂地铁站（开福区）｜面积：76㎡｜户型：2室2厅  \n💰 租金：**2208元/月**  \n✨ 亮点：**性价比超高！近地铁、精装、无中介费、可月付**，小区为楚天世纪城，交通便利，适合预算有限但希望住得舒服的朋友。\n\n---\n\n这三套分别代表了**江景便利型、品质舒适型、高性价比型**，您可以根据自己的预算和区域偏好做选择。\n\n如果您有更具体的需求（比如“只要岳麓区”“预算不超过2500”“必须近地铁”等），欢迎告诉我，我可以立刻为您精准筛选！\n\n另外，需要我帮您查看其中某一套的**详细信息**（如楼层、家具配置、房东评价等）吗？', '2026-05-11 16:18:58');
INSERT INTO `chat_message` VALUES (59, 23, 'user', '帮我推荐一个两居室的房子', '2026-05-11 16:22:53');
INSERT INTO `chat_message` VALUES (60, 23, 'assistant', '太好了！我在热门房源中为您筛选出了**3套高人气的两居室**，都是近期浏览量很高的优质房源，信息如下：\n\n---\n\n🏠 **【包租婆宿懒公寓 · 保利天禧】**  \n📍 区域：岳麓（近六沟垅地铁）｜面积：38㎡｜户型：2室1厅  \n💰 租金：**2750元/月**  \n✨ 亮点：**精装交付、近地铁、靠近山姆超市 & 万象城、支持月付、无中介费**，还是一线江景房！虽然面积不大，但布局紧凑，适合小家庭或情侣。\n\n---\n\n🏠 **【北辰中央公园(慧辰园) · 精装南向两居】**  \n📍 区域：**天心区·省政府板块**｜面积：95㎡｜户型：2室2厅｜朝南  \n💰 租金：**3000元/月**  \n✨ 亮点：**南北通透、精装品质小区、面积宽敞**，适合追求舒适度的家庭。周边配套成熟，生活便利。\n\n---\n\n🏠 **【华佑e家 · 万国城店】**  \n📍 区域：开福（近马厂地铁站）｜面积：76㎡｜户型：2室2厅  \n💰 租金：**2208元/月**  \n✨ 亮点：**近地铁、精装、无中介费、可月付**，性价比非常高！小区为楚天世纪城，生活氛围浓厚。\n\n---\n\n这三套分别位于**岳麓、天心、开福**，价格从2200+到3000元不等，都支持整租且装修良好。\n\n✅ 如果您对其中某一套感兴趣，我可以为您调取**详细房源信息**（包括实拍图、具体楼层、配套设施等）；  \n✅ 或者，如果您有更明确的预算或区域偏好，我也可以**重新精准搜索**符合您条件的两居室！\n\n请问您想进一步了解哪一套？或者告诉我您的具体需求，我来优化推荐！ 😊', '2026-05-11 16:23:13');
INSERT INTO `chat_message` VALUES (62, 13, 'user', '你能推荐一些靠近地铁的房子吗', '2026-05-11 17:15:49');
INSERT INTO `chat_message` VALUES (63, 13, 'assistant', '太好了！我从热门房源中为您筛选出**3套明确靠近地铁、且近期很受欢迎的近地铁房源**，覆盖不同预算和区域，供您参考：\n\n---\n\n🏠 **【高性价比·马厂地铁口】华佑e家 万国城店**  \n📍 区域：楚天世纪城（近**马厂地铁站**）｜面积：76㎡｜户型：2室2厅  \n💰 租金：**2208元/月**（可月付，无中介费！）  \n✨ 亮点：精装交付、交通便利，适合预算有限但追求品质的租客。\n\n---\n\n🏠 **【江景+地铁双优】包租婆宿懒公寓 · 保利天禧**  \n📍 区域：近**六沟垅地铁站**｜面积：38㎡｜户型：2室1厅  \n💰 租金：**2750元/月**（支持月付，无中介）  \n✨ 亮点：一线江景、步行可达地铁，周边有山姆超市+万象城，生活超便利！\n\n---\n\n🏠 **【高端大平层·地铁便捷】穗露公寓 · 越秀湘江星汇城**  \n📍 区域：近地铁（具体线路未注明，但标注 subway=1）｜面积：186㎡｜户型：4室2厅  \n💰 租金：**6600元/月**  \n✨ 亮点：豪装大平层，适合家庭或多人合租，空间宽敞，品质感强。\n\n---\n\n✅ 这些房源都明确标注了“近地铁”（subway=1），且是当前平台浏览量最高的热门选择。\n\n如果您有**特定区域偏好**（比如只想看岳麓区或天心区），或者希望**价格控制在某个范围**（如3000元以内），我可以立即为您精准搜索更多选项！需要吗？😊', '2026-05-11 17:16:09');
INSERT INTO `chat_message` VALUES (71, 26, 'user', '你好，请问你能推荐一些岳麓区的2000元左右的房子吗', '2026-05-23 10:46:41');
INSERT INTO `chat_message` VALUES (72, 26, 'assistant', '太好了！我为您找到了一套符合预算的岳麓区房源，具体信息如下：\n\n🏠 **合租·盘锦小区 2室1厅 南**  \n📍 区域：岳麓区德政园 | 小区：盘锦小区  \n📏 面积：83㎡ | 户型：2室1厅1卫 | 朝向：南  \n💰 租金：2000元/月  \n✨ 装修情况：简装 | 出租方式：整租  \n📞 联系房东：张先生 136****8915  \n\n这套房子性价比很高，83㎡的面积在2000元价位非常实惠，而且是整租形式，私密性更好。朝南的户型采光也不错。\n\n不过我注意到这套房源显示“不近地铁”，如果您对交通便利性有要求，我可以帮您查询周边配套设施或通勤情况。另外，如果您希望看更多房源选择，也可以调整价格范围或增加其他筛选条件。\n\n请问您对这套房子感兴趣吗？或者需要了解更多细节？', '2026-05-23 10:46:54');
INSERT INTO `chat_message` VALUES (73, 26, 'user', '你觉得今天的天气适合看房吗', '2026-05-23 10:47:24');
INSERT INTO `chat_message` VALUES (74, 26, 'assistant', '根据最新天气数据，今天（5月23日）长沙是🌧️**小雨天气**，气温24°C，湿度高达98%，体感比较闷湿。\n\n不过——**这其实是个看房的好时机！**\n\n正如系统提示所说：**雨天是检验房屋防水性能的绝佳机会**！您可以重点观察：\n- 天花板、墙角是否有渗水或发霉痕迹\n- 窗台、阳台是否漏水\n- 下水管道排水是否顺畅\n\n如果您计划今天去看房，建议：\n✅ 带上伞和防滑鞋  \n✅ 优先查看顶楼或靠外墙的房间  \n✅ 白天10–16点之间温度相对舒适（最高31°C）\n\n未来两天也持续有小雨，所以**今天看房并不吃亏**，反而能发现晴天看不到的问题！\n\n需要我帮您预约这套岳麓区的房子看房，或者查询它的详细防水/装修情况吗？', '2026-05-23 10:47:35');
INSERT INTO `chat_message` VALUES (75, 26, 'user', '你能推荐一下附近有地铁的房子吗', '2026-05-24 09:17:51');
INSERT INTO `chat_message` VALUES (76, 26, 'assistant', '很抱歉，在岳麓区 **1800–2200元/月** 的价格区间内，目前**没有找到靠近地铁的房源**。这主要是因为岳麓区临近地铁（如2号线、4号线）的小区租金普遍略高。\n\n不过别担心！我有几个实用建议供您参考：\n\n### ✅ 方案一：**稍微提高预算至2500元左右**\n岳麓区近地铁的合租房源大多在2300–2800元之间。若您能小幅增加预算，选择会多很多。\n\n### ✅ 方案二：**考虑相邻区域——天心区或雨花区**\n这两个区域地铁覆盖密集（1/2/4号线交汇），且2000元预算更容易找到近地铁的房子。例如：\n- **天心区**：靠近五一广场、南门口，生活便利\n- **雨花区**：高铁南站、万家丽商圈周边，通勤高效\n\n### ✅ 方案三：**保持岳麓区，接受“步行10–15分钟到地铁”**\n有些房源虽未标记“近地铁”，但实际距离地铁站仅800–1000米，性价比更高。\n\n---\n\n请问您更倾向哪种方案？我可以立即为您查询：\n1. 岳麓区 **2500元以内** 近地铁房源  \n2. **天心区或雨花区** 2000元左右近地铁房源  \n3. 岳麓区 **步行可达地铁** 的高性价比房源  \n\n欢迎告诉我您的偏好！🚇', '2026-05-24 09:18:08');

-- ----------------------------
-- Table structure for chat_session
-- ----------------------------
DROP TABLE IF EXISTS `chat_session`;
CREATE TABLE `chat_session`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '关联 user_info 表的 id',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '新对话' COMMENT '会话标题，可取第一句话',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_session_user`(`user_id` ASC) USING BTREE,
  CONSTRAINT `fk_session_user` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 27 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chat_session
-- ----------------------------
INSERT INTO `chat_session` VALUES (1, 4, '你好，请问你能推荐一些岳麓区的...', '2026-04-28 14:27:01', '2026-05-08 17:00:45');
INSERT INTO `chat_session` VALUES (2, 4, '你能推荐一些靠近地铁的房源吗', '2026-04-28 14:29:25', '2026-04-28 14:29:52');
INSERT INTO `chat_session` VALUES (10, 11, '你好，请问今天天气如何，能推荐...', '2026-04-29 20:08:42', '2026-04-30 17:51:04');
INSERT INTO `chat_session` VALUES (11, 4, '你能推荐一些芙蓉区的3000元...', '2026-04-29 21:12:48', '2026-04-29 21:13:10');
INSERT INTO `chat_session` VALUES (12, 11, '你好，你能推荐一些在芙蓉区的，...', '2026-05-02 14:57:30', '2026-05-02 14:57:47');
INSERT INTO `chat_session` VALUES (13, 11, '你好，请问今天天气适合看房吗', '2026-05-09 16:13:41', '2026-05-11 17:16:09');
INSERT INTO `chat_session` VALUES (14, 19, '帮我推荐一个两居室的房子', '2026-05-11 15:42:07', '2026-05-11 15:42:12');
INSERT INTO `chat_session` VALUES (15, 19, '帮我推荐一个两居室的房子', '2026-05-11 15:43:25', '2026-05-11 15:43:47');
INSERT INTO `chat_session` VALUES (16, 19, '帮我推荐一个两居室的房子', '2026-05-11 15:48:25', '2026-05-11 15:48:30');
INSERT INTO `chat_session` VALUES (17, 19, '帮我推荐一个两居室的房子', '2026-05-11 15:49:43', '2026-05-11 15:50:04');
INSERT INTO `chat_session` VALUES (18, 19, '帮我推荐一个两居室的房子', '2026-05-11 15:51:35', '2026-05-11 15:51:40');
INSERT INTO `chat_session` VALUES (19, 19, '帮我推荐一个两居室的房子', '2026-05-11 16:12:41', '2026-05-11 16:12:48');
INSERT INTO `chat_session` VALUES (20, 19, '帮我推荐一个两居室的房子', '2026-05-11 16:15:11', '2026-05-11 16:15:16');
INSERT INTO `chat_session` VALUES (21, 19, '帮我推荐一个两居室的房子', '2026-05-11 16:16:45', '2026-05-11 16:16:49');
INSERT INTO `chat_session` VALUES (22, 19, '帮我推荐一个两居室的房子', '2026-05-11 16:18:37', '2026-05-11 16:18:57');
INSERT INTO `chat_session` VALUES (23, 19, '帮我推荐一个两居室的房子', '2026-05-11 16:22:53', '2026-05-11 16:23:12');
INSERT INTO `chat_session` VALUES (26, 11, '你好，请问你能推荐一些岳麓区的...', '2026-05-23 10:46:41', '2026-05-24 09:18:08');

-- ----------------------------
-- Table structure for comment
-- ----------------------------
DROP TABLE IF EXISTS `comment`;
CREATE TABLE `comment`  (
  `comment_id` int NOT NULL AUTO_INCREMENT,
  `house_id` int NOT NULL COMMENT '房屋的id',
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '留言人名字',
  `type` int NOT NULL COMMENT '留言人类型,1:租客，2:房东',
  `desc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '留言内容',
  `at` int NULL DEFAULT NULL COMMENT '@哪条留言，前端显示为@谁，选填',
  `time` datetime NOT NULL COMMENT '留言时间',
  PRIMARY KEY (`comment_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 165 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of comment
-- ----------------------------
INSERT INTO `comment` VALUES (13, 10, '租客1', 1, '这是第1条留言，房东房东C你好！', NULL, '2025-04-26 17:39:14');
INSERT INTO `comment` VALUES (14, 10, '租客2', 1, '这是第2条留言，房东房东C你好！', NULL, '2025-04-25 17:39:14');
INSERT INTO `comment` VALUES (15, 10, '租客3', 1, '这是第3条留言，房东房东C你好！', NULL, '2025-04-24 17:39:14');
INSERT INTO `comment` VALUES (16, 10, '租客4', 1, '这是第4条留言，房东房东C你好！', NULL, '2025-04-23 17:39:14');
INSERT INTO `comment` VALUES (17, 10, '租客5', 1, '这是第5条留言，房东房东C你好！', NULL, '2025-04-22 17:39:14');
INSERT INTO `comment` VALUES (18, 10, '租客6', 1, '这是第6条留言，房东房东C你好！', NULL, '2025-04-21 17:39:14');
INSERT INTO `comment` VALUES (19, 10, '租客7', 1, '这是第7条留言，房东房东C你好！', NULL, '2025-04-20 17:39:14');
INSERT INTO `comment` VALUES (20, 10, '租客8', 1, '这是第8条留言，房东房东C你好！', NULL, '2025-04-19 17:39:14');
INSERT INTO `comment` VALUES (21, 10, '租客9', 1, '这是第9条留言，房东房东C你好！', NULL, '2025-04-18 17:39:14');
INSERT INTO `comment` VALUES (22, 10, '租客10', 1, '这是第10条留言，房东房东C你好！', NULL, '2025-04-17 17:39:14');
INSERT INTO `comment` VALUES (23, 9, '租客1', 1, '这是第1条留言，房东房东B你好！', NULL, '2025-04-26 17:39:14');
INSERT INTO `comment` VALUES (24, 9, '租客2', 1, '这是第2条留言，房东房东B你好！', NULL, '2025-04-25 17:39:14');
INSERT INTO `comment` VALUES (25, 9, '租客3', 1, '这是第3条留言，房东房东B你好！', NULL, '2025-04-24 17:39:14');
INSERT INTO `comment` VALUES (26, 9, '租客4', 1, '这是第4条留言，房东房东B你好！', NULL, '2025-04-23 17:39:14');
INSERT INTO `comment` VALUES (27, 9, '租客5', 1, '这是第5条留言，房东房东B你好！', NULL, '2025-04-22 17:39:14');
INSERT INTO `comment` VALUES (28, 9, '租客6', 1, '这是第6条留言，房东房东B你好！', NULL, '2025-04-21 17:39:14');
INSERT INTO `comment` VALUES (29, 9, '租客7', 1, '这是第7条留言，房东房东B你好！', NULL, '2025-04-20 17:39:14');
INSERT INTO `comment` VALUES (30, 9, '租客8', 1, '这是第8条留言，房东房东B你好！', NULL, '2025-04-19 17:39:14');
INSERT INTO `comment` VALUES (31, 9, '租客9', 1, '这是第9条留言，房东房东B你好！', NULL, '2025-04-18 17:39:14');
INSERT INTO `comment` VALUES (32, 9, '租客10', 1, '这是第10条留言，房东房东B你好！', NULL, '2025-04-17 17:39:14');
INSERT INTO `comment` VALUES (33, 8, '租客1', 1, '这是第1条留言，房东landlord3你好！', NULL, '2025-04-26 17:39:14');
INSERT INTO `comment` VALUES (34, 8, '租客2', 1, '这是第2条留言，房东landlord3你好！', NULL, '2025-04-25 17:39:14');
INSERT INTO `comment` VALUES (35, 8, '租客3', 1, '这是第3条留言，房东landlord3你好！', NULL, '2025-04-24 17:39:14');
INSERT INTO `comment` VALUES (36, 8, '租客4', 1, '这是第4条留言，房东landlord3你好！', NULL, '2025-04-23 17:39:14');
INSERT INTO `comment` VALUES (37, 8, '租客5', 1, '这是第5条留言，房东landlord3你好！', NULL, '2025-04-22 17:39:14');
INSERT INTO `comment` VALUES (38, 8, '租客6', 1, '这是第6条留言，房东landlord3你好！', NULL, '2025-04-21 17:39:14');
INSERT INTO `comment` VALUES (39, 8, '租客7', 1, '这是第7条留言，房东landlord3你好！', NULL, '2025-04-20 17:39:14');
INSERT INTO `comment` VALUES (40, 8, '租客8', 1, '这是第8条留言，房东landlord3你好！', NULL, '2025-04-19 17:39:14');
INSERT INTO `comment` VALUES (41, 8, '租客9', 1, '这是第9条留言，房东landlord3你好！', NULL, '2025-04-18 17:39:14');
INSERT INTO `comment` VALUES (42, 8, '租客10', 1, '这是第10条留言，房东landlord3你好！', NULL, '2025-04-17 17:39:14');
INSERT INTO `comment` VALUES (43, 7, '租客1', 1, '这是第1条留言，房东landlord你好！', NULL, '2025-04-26 17:39:14');
INSERT INTO `comment` VALUES (44, 7, '租客2', 1, '这是第2条留言，房东landlord你好！', NULL, '2025-04-25 17:39:14');
INSERT INTO `comment` VALUES (45, 7, '租客3', 1, '这是第3条留言，房东landlord你好！', NULL, '2025-04-24 17:39:14');
INSERT INTO `comment` VALUES (46, 7, '租客4', 1, '这是第4条留言，房东landlord你好！', NULL, '2025-04-23 17:39:14');
INSERT INTO `comment` VALUES (47, 7, '租客5', 1, '这是第5条留言，房东landlord你好！', NULL, '2025-04-22 17:39:14');
INSERT INTO `comment` VALUES (48, 7, '租客6', 1, '这是第6条留言，房东landlord你好！', NULL, '2025-04-21 17:39:14');
INSERT INTO `comment` VALUES (49, 7, '租客7', 1, '这是第7条留言，房东landlord你好！', NULL, '2025-04-20 17:39:14');
INSERT INTO `comment` VALUES (50, 7, '租客8', 1, '这是第8条留言，房东landlord你好！', NULL, '2025-04-19 17:39:14');
INSERT INTO `comment` VALUES (51, 7, '租客9', 1, '这是第9条留言，房东landlord你好！', NULL, '2025-04-18 17:39:14');
INSERT INTO `comment` VALUES (52, 7, '租客10', 1, '这是第10条留言，房东landlord你好！', NULL, '2025-04-17 17:39:14');
INSERT INTO `comment` VALUES (53, 6, '租客1', 1, '这是第1条留言，房东landlord你好！', NULL, '2025-04-26 17:39:14');
INSERT INTO `comment` VALUES (54, 6, '租客2', 1, '这是第2条留言，房东landlord你好！', NULL, '2025-04-25 17:39:14');
INSERT INTO `comment` VALUES (55, 6, '租客3', 1, '这是第3条留言，房东landlord你好！', NULL, '2025-04-24 17:39:14');
INSERT INTO `comment` VALUES (56, 6, '租客4', 1, '这是第4条留言，房东landlord你好！', NULL, '2025-04-23 17:39:14');
INSERT INTO `comment` VALUES (57, 6, '租客5', 1, '这是第5条留言，房东landlord你好！', NULL, '2025-04-22 17:39:14');
INSERT INTO `comment` VALUES (58, 6, '租客6', 1, '这是第6条留言，房东landlord你好！', NULL, '2025-04-21 17:39:14');
INSERT INTO `comment` VALUES (59, 6, '租客7', 1, '这是第7条留言，房东landlord你好！', NULL, '2025-04-20 17:39:14');
INSERT INTO `comment` VALUES (60, 6, '租客8', 1, '这是第8条留言，房东landlord你好！', NULL, '2025-04-19 17:39:14');
INSERT INTO `comment` VALUES (61, 6, '租客9', 1, '这是第9条留言，房东landlord你好！', NULL, '2025-04-18 17:39:14');
INSERT INTO `comment` VALUES (62, 6, '租客10', 1, '这是第10条留言，房东landlord你好！', NULL, '2025-04-17 17:39:14');
INSERT INTO `comment` VALUES (63, 5, '租客1', 1, '这是第1条留言，房东landlord你好！', NULL, '2025-04-26 17:39:14');
INSERT INTO `comment` VALUES (64, 5, '租客2', 1, '这是第2条留言，房东landlord你好！', NULL, '2025-04-25 17:39:14');
INSERT INTO `comment` VALUES (65, 5, '租客3', 1, '这是第3条留言，房东landlord你好！', NULL, '2025-04-24 17:39:14');
INSERT INTO `comment` VALUES (66, 5, '租客4', 1, '这是第4条留言，房东landlord你好！', NULL, '2025-04-23 17:39:14');
INSERT INTO `comment` VALUES (67, 5, '租客5', 1, '这是第5条留言，房东landlord你好！', NULL, '2025-04-22 17:39:14');
INSERT INTO `comment` VALUES (68, 5, '租客6', 1, '这是第6条留言，房东landlord你好！', NULL, '2025-04-21 17:39:14');
INSERT INTO `comment` VALUES (69, 5, '租客7', 1, '这是第7条留言，房东landlord你好！', NULL, '2025-04-20 17:39:14');
INSERT INTO `comment` VALUES (70, 5, '租客8', 1, '这是第8条留言，房东landlord你好！', NULL, '2025-04-19 17:39:14');
INSERT INTO `comment` VALUES (71, 5, '租客9', 1, '这是第9条留言，房东landlord你好！', NULL, '2025-04-18 17:39:14');
INSERT INTO `comment` VALUES (72, 5, '租客10', 1, '这是第10条留言，房东landlord你好！', NULL, '2025-04-17 17:39:14');
INSERT INTO `comment` VALUES (73, 10, '租客1', 1, '这是第1条留言，房东房东C你好！', NULL, '2025-04-26 17:46:06');
INSERT INTO `comment` VALUES (74, 10, '租客2', 1, '这是第2条留言，房东房东C你好！', NULL, '2025-04-25 17:46:06');
INSERT INTO `comment` VALUES (75, 10, '租客3', 1, '这是第3条留言，房东房东C你好！', NULL, '2025-04-24 17:46:06');
INSERT INTO `comment` VALUES (76, 10, '租客4', 1, '这是第4条留言，房东房东C你好！', NULL, '2025-04-23 17:46:06');
INSERT INTO `comment` VALUES (77, 10, '租客5', 1, '这是第5条留言，房东房东C你好！', NULL, '2025-04-22 17:46:06');
INSERT INTO `comment` VALUES (78, 10, '租客6', 1, '这是第6条留言，房东房东C你好！', NULL, '2025-04-21 17:46:06');
INSERT INTO `comment` VALUES (79, 10, '租客7', 1, '这是第7条留言，房东房东C你好！', NULL, '2025-04-20 17:46:06');
INSERT INTO `comment` VALUES (80, 10, '租客8', 1, '这是第8条留言，房东房东C你好！', NULL, '2025-04-19 17:46:06');
INSERT INTO `comment` VALUES (81, 10, '租客9', 1, '这是第9条留言，房东房东C你好！', NULL, '2025-04-18 17:46:06');
INSERT INTO `comment` VALUES (82, 10, '租客10', 1, '这是第10条留言，房东房东C你好！', NULL, '2025-04-17 17:46:06');
INSERT INTO `comment` VALUES (83, 9, '租客1', 1, '这是第1条留言，房东房东B你好！', NULL, '2025-04-26 17:46:06');
INSERT INTO `comment` VALUES (84, 9, '租客2', 1, '这是第2条留言，房东房东B你好！', NULL, '2025-04-25 17:46:06');
INSERT INTO `comment` VALUES (85, 9, '租客3', 1, '这是第3条留言，房东房东B你好！', NULL, '2025-04-24 17:46:06');
INSERT INTO `comment` VALUES (86, 9, '租客4', 1, '这是第4条留言，房东房东B你好！', NULL, '2025-04-23 17:46:06');
INSERT INTO `comment` VALUES (87, 9, '租客5', 1, '这是第5条留言，房东房东B你好！', NULL, '2025-04-22 17:46:06');
INSERT INTO `comment` VALUES (88, 9, '租客6', 1, '这是第6条留言，房东房东B你好！', NULL, '2025-04-21 17:46:06');
INSERT INTO `comment` VALUES (89, 9, '租客7', 1, '这是第7条留言，房东房东B你好！', NULL, '2025-04-20 17:46:06');
INSERT INTO `comment` VALUES (90, 9, '租客8', 1, '这是第8条留言，房东房东B你好！', NULL, '2025-04-19 17:46:06');
INSERT INTO `comment` VALUES (91, 9, '租客9', 1, '这是第9条留言，房东房东B你好！', NULL, '2025-04-18 17:46:06');
INSERT INTO `comment` VALUES (92, 9, '租客10', 1, '这是第10条留言，房东房东B你好！', NULL, '2025-04-17 17:46:06');
INSERT INTO `comment` VALUES (93, 8, '租客1', 1, '这是第1条留言，房东landlord3你好！', NULL, '2025-04-26 17:46:06');
INSERT INTO `comment` VALUES (94, 8, '租客2', 1, '这是第2条留言，房东landlord3你好！', NULL, '2025-04-25 17:46:06');
INSERT INTO `comment` VALUES (95, 8, '租客3', 1, '这是第3条留言，房东landlord3你好！', NULL, '2025-04-24 17:46:06');
INSERT INTO `comment` VALUES (96, 8, '租客4', 1, '这是第4条留言，房东landlord3你好！', NULL, '2025-04-23 17:46:06');
INSERT INTO `comment` VALUES (97, 8, '租客5', 1, '这是第5条留言，房东landlord3你好！', NULL, '2025-04-22 17:46:06');
INSERT INTO `comment` VALUES (98, 8, '租客6', 1, '这是第6条留言，房东landlord3你好！', NULL, '2025-04-21 17:46:06');
INSERT INTO `comment` VALUES (99, 8, '租客7', 1, '这是第7条留言，房东landlord3你好！', NULL, '2025-04-20 17:46:06');
INSERT INTO `comment` VALUES (100, 8, '租客8', 1, '这是第8条留言，房东landlord3你好！', NULL, '2025-04-19 17:46:06');
INSERT INTO `comment` VALUES (101, 8, '租客9', 1, '这是第9条留言，房东landlord3你好！', NULL, '2025-04-18 17:46:06');
INSERT INTO `comment` VALUES (102, 8, '租客10', 1, '这是第10条留言，房东landlord3你好！', NULL, '2025-04-17 17:46:06');
INSERT INTO `comment` VALUES (103, 7, '租客1', 1, '这是第1条留言，房东landlord你好！', NULL, '2025-04-26 17:46:06');
INSERT INTO `comment` VALUES (104, 7, '租客2', 1, '这是第2条留言，房东landlord你好！', NULL, '2025-04-25 17:46:06');
INSERT INTO `comment` VALUES (105, 7, '租客3', 1, '这是第3条留言，房东landlord你好！', NULL, '2025-04-24 17:46:06');
INSERT INTO `comment` VALUES (106, 7, '租客4', 1, '这是第4条留言，房东landlord你好！', NULL, '2025-04-23 17:46:06');
INSERT INTO `comment` VALUES (107, 7, '租客5', 1, '这是第5条留言，房东landlord你好！', NULL, '2025-04-22 17:46:06');
INSERT INTO `comment` VALUES (108, 7, '租客6', 1, '这是第6条留言，房东landlord你好！', NULL, '2025-04-21 17:46:06');
INSERT INTO `comment` VALUES (109, 7, '租客7', 1, '这是第7条留言，房东landlord你好！', NULL, '2025-04-20 17:46:06');
INSERT INTO `comment` VALUES (110, 7, '租客8', 1, '这是第8条留言，房东landlord你好！', NULL, '2025-04-19 17:46:06');
INSERT INTO `comment` VALUES (111, 7, '租客9', 1, '这是第9条留言，房东landlord你好！', NULL, '2025-04-18 17:46:06');
INSERT INTO `comment` VALUES (112, 7, '租客10', 1, '这是第10条留言，房东landlord你好！', NULL, '2025-04-17 17:46:06');
INSERT INTO `comment` VALUES (113, 6, '租客1', 1, '这是第1条留言，房东landlord你好！', NULL, '2025-04-26 17:46:06');
INSERT INTO `comment` VALUES (114, 6, '租客2', 1, '这是第2条留言，房东landlord你好！', NULL, '2025-04-25 17:46:06');
INSERT INTO `comment` VALUES (115, 6, '租客3', 1, '这是第3条留言，房东landlord你好！', NULL, '2025-04-24 17:46:06');
INSERT INTO `comment` VALUES (116, 6, '租客4', 1, '这是第4条留言，房东landlord你好！', NULL, '2025-04-23 17:46:06');
INSERT INTO `comment` VALUES (117, 6, '租客5', 1, '这是第5条留言，房东landlord你好！', NULL, '2025-04-22 17:46:06');
INSERT INTO `comment` VALUES (118, 6, '租客6', 1, '这是第6条留言，房东landlord你好！', NULL, '2025-04-21 17:46:06');
INSERT INTO `comment` VALUES (119, 6, '租客7', 1, '这是第7条留言，房东landlord你好！', NULL, '2025-04-20 17:46:06');
INSERT INTO `comment` VALUES (120, 6, '租客8', 1, '这是第8条留言，房东landlord你好！', NULL, '2025-04-19 17:46:06');
INSERT INTO `comment` VALUES (121, 6, '租客9', 1, '这是第9条留言，房东landlord你好！', NULL, '2025-04-18 17:46:06');
INSERT INTO `comment` VALUES (122, 6, '租客10', 1, '这是第10条留言，房东landlord你好！', NULL, '2025-04-17 17:46:06');
INSERT INTO `comment` VALUES (123, 5, '租客1', 1, '这是第1条留言，房东landlord你好！', NULL, '2025-04-26 17:46:06');
INSERT INTO `comment` VALUES (124, 5, '租客2', 1, '这是第2条留言，房东landlord你好！', NULL, '2025-04-25 17:46:06');
INSERT INTO `comment` VALUES (125, 5, '租客3', 1, '这是第3条留言，房东landlord你好！', NULL, '2025-04-24 17:46:06');
INSERT INTO `comment` VALUES (126, 5, '租客4', 1, '这是第4条留言，房东landlord你好！', NULL, '2025-04-23 17:46:06');
INSERT INTO `comment` VALUES (127, 5, '租客5', 1, '这是第5条留言，房东landlord你好！', NULL, '2025-04-22 17:46:06');
INSERT INTO `comment` VALUES (128, 5, '租客6', 1, '这是第6条留言，房东landlord你好！', NULL, '2025-04-21 17:46:06');
INSERT INTO `comment` VALUES (129, 5, '租客7', 1, '这是第7条留言，房东landlord你好！', NULL, '2025-04-20 17:46:06');
INSERT INTO `comment` VALUES (130, 5, '租客8', 1, '这是第8条留言，房东landlord你好！', NULL, '2025-04-19 17:46:06');
INSERT INTO `comment` VALUES (131, 5, '租客9', 1, '这是第9条留言，房东landlord你好！', NULL, '2025-04-18 17:46:06');
INSERT INTO `comment` VALUES (132, 5, '租客10', 1, '这是第10条留言，房东landlord你好！', NULL, '2025-04-17 17:46:06');
INSERT INTO `comment` VALUES (133, 6, 'qwe', 1, 'ggg', NULL, '2025-04-26 18:55:38');
INSERT INTO `comment` VALUES (134, 5, 'qwe', 1, 'ya', NULL, '2025-04-26 19:03:47');
INSERT INTO `comment` VALUES (135, 5, 'qwe', 1, 'zg', NULL, '2025-04-26 19:14:14');
INSERT INTO `comment` VALUES (136, 5, 'qwe', 1, 'fff', NULL, '2025-04-26 19:16:53');
INSERT INTO `comment` VALUES (137, 5, 'qwe', 1, 'www', NULL, '2025-04-26 19:17:00');
INSERT INTO `comment` VALUES (138, 10, 'man', 1, 'hello', NULL, '2025-05-18 17:23:38');
INSERT INTO `comment` VALUES (139, 1, 'Ylfmoonn', 1, '吖', NULL, '2025-06-02 14:30:43');
INSERT INTO `comment` VALUES (140, 1, 'comment_tester_e495fc', 1, '这是一条自动化测试评论', NULL, '2026-05-11 15:42:12');
INSERT INTO `comment` VALUES (141, 1, 'comment_tester_ea99f9', 1, '这是一条自动化测试评论', NULL, '2026-05-11 15:43:48');
INSERT INTO `comment` VALUES (142, 1, 'comment_tester_cd6263', 1, '这是一条自动化测试评论', NULL, '2026-05-11 15:48:31');
INSERT INTO `comment` VALUES (143, 1, 'comment_tester_c1a57a', 1, '这是一条自动化测试评论', NULL, '2026-05-11 15:50:04');
INSERT INTO `comment` VALUES (144, 1, 'comment_tester_7a6788', 1, '这是一条自动化测试评论', NULL, '2026-05-11 15:51:40');
INSERT INTO `comment` VALUES (145, 1, 'comment_user_0020b2', 1, '房子很不错，交通便利，推荐！', NULL, '2026-05-11 16:12:48');
INSERT INTO `comment` VALUES (146, 1, 'comment_user_47684f', 2, '感谢好评，欢迎再次入住！', NULL, '2026-05-11 16:12:48');
INSERT INTO `comment` VALUES (147, 1, 'comment_user_5c6893', 1, '普通评论，不回复任何人', NULL, '2026-05-11 16:12:48');
INSERT INTO `comment` VALUES (148, 1, 'comment_user_e4d21c', 1, 'at字段为空的评论', NULL, '2026-05-11 16:12:48');
INSERT INTO `comment` VALUES (149, 1, 'comment_user_dc1ef1', 1, '房子很不错，交通便利，推荐！', NULL, '2026-05-11 16:15:16');
INSERT INTO `comment` VALUES (150, 1, 'comment_user_7b4fd2', 2, '感谢好评，欢迎再次入住！', NULL, '2026-05-11 16:15:17');
INSERT INTO `comment` VALUES (151, 1, 'comment_user_71d8db', 1, '普通评论，不回复任何人', NULL, '2026-05-11 16:15:17');
INSERT INTO `comment` VALUES (152, 1, 'comment_user_11c431', 1, 'at字段为空的评论', NULL, '2026-05-11 16:15:17');
INSERT INTO `comment` VALUES (153, 1, 'comment_user_9dc8ea', 1, '房子很不错，交通便利，推荐！', NULL, '2026-05-11 16:16:50');
INSERT INTO `comment` VALUES (154, 1, 'comment_user_972650', 2, '感谢好评，欢迎再次入住！', NULL, '2026-05-11 16:16:50');
INSERT INTO `comment` VALUES (155, 1, 'comment_user_255158', 1, '普通评论，不回复任何人', NULL, '2026-05-11 16:16:50');
INSERT INTO `comment` VALUES (156, 1, 'comment_user_66a864', 1, 'at字段为空的评论', NULL, '2026-05-11 16:16:50');
INSERT INTO `comment` VALUES (157, 1, 'comment_user_25a70b', 1, '房子很不错，交通便利，推荐！', NULL, '2026-05-11 16:18:58');
INSERT INTO `comment` VALUES (158, 1, 'comment_user_8f9ce8', 2, '感谢好评，欢迎再次入住！', NULL, '2026-05-11 16:18:58');
INSERT INTO `comment` VALUES (159, 1, 'comment_user_381bf0', 1, '普通评论，不回复任何人', NULL, '2026-05-11 16:18:58');
INSERT INTO `comment` VALUES (160, 1, 'comment_user_ad30c6', 1, 'at字段为空的评论', NULL, '2026-05-11 16:18:58');
INSERT INTO `comment` VALUES (161, 1, 'comment_user_a84073', 1, '房子很不错，交通便利，推荐！', NULL, '2026-05-11 16:23:13');
INSERT INTO `comment` VALUES (162, 1, 'comment_user_fb51d6', 2, '感谢好评，欢迎再次入住！', NULL, '2026-05-11 16:23:13');
INSERT INTO `comment` VALUES (163, 1, 'comment_user_7ad4a5', 1, '普通评论，不回复任何人', NULL, '2026-05-11 16:23:13');
INSERT INTO `comment` VALUES (164, 1, 'comment_user_fb66cf', 1, 'at字段为空的评论', NULL, '2026-05-11 16:23:13');

-- ----------------------------
-- Table structure for contract
-- ----------------------------
DROP TABLE IF EXISTS `contract`;
CREATE TABLE `contract`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `rentValue` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `purpose` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `startDate` datetime NULL DEFAULT NULL,
  `endDate` datetime NULL DEFAULT NULL,
  `landlordName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `landlordId` int NULL DEFAULT NULL,
  `landlordPhone` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `tenantName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `tenantId` int NULL DEFAULT NULL,
  `tenantPhone` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `formattedRent` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `currentDate` datetime NULL DEFAULT NULL,
  `houseId` int NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_contract_houseId`(`houseId` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 75 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of contract
-- ----------------------------
INSERT INTO `contract` VALUES (1, '10251', '居住', '2025-04-30 16:00:00', '2025-05-30 16:00:00', '', NULL, '', '', NULL, '', '壹万零仟贰佰伍拾壹元整', '2025-05-18 00:00:00', NULL);
INSERT INTO `contract` VALUES (2, '3200', '办公', '2025-04-30 16:00:00', '2025-05-01 16:00:00', '', NULL, '', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-23 00:00:00', NULL);
INSERT INTO `contract` VALUES (3, '3200', '居住', '2025-05-29 16:00:00', '2025-05-30 16:00:00', '张先生', NULL, '13800001234', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-23 00:00:00', NULL);
INSERT INTO `contract` VALUES (4, '3200', '居住', '2025-05-08 16:00:00', '2025-05-30 16:00:00', '张先生', NULL, '13800001234', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-23 00:00:00', NULL);
INSERT INTO `contract` VALUES (5, '3200', '居住', '2025-05-22 16:00:00', '2025-05-30 16:00:00', '张先生', NULL, '13800001234', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-23 00:00:00', NULL);
INSERT INTO `contract` VALUES (6, '3200', '居住', '2025-04-30 16:00:00', '2025-05-30 16:00:00', '张先生', NULL, '13800001234', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-23 00:00:00', NULL);
INSERT INTO `contract` VALUES (7, '3200', '居住', '2025-05-29 16:00:00', '2025-08-14 16:00:00', '龟壳公寓', NULL, '13800005678', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-26 00:00:00', NULL);
INSERT INTO `contract` VALUES (8, '3200', '办公', '2025-05-23 16:00:00', '2025-05-30 16:00:00', '龟壳公寓', NULL, '13800005678', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-26 00:00:00', NULL);
INSERT INTO `contract` VALUES (9, '3200', '办公', '2025-04-30 16:00:00', '2025-05-01 16:00:00', '张先生', NULL, '13800001234', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-26 00:00:00', NULL);
INSERT INTO `contract` VALUES (10, '3200', '居住', '2025-05-08 16:00:00', '2025-05-01 16:00:00', '丁先生', NULL, '15612340015', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-29 00:00:00', NULL);
INSERT INTO `contract` VALUES (11, '3200', '居住', '2025-05-08 16:00:00', '2025-05-01 16:00:00', '丁先生', NULL, '15612340015', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-29 00:00:00', NULL);
INSERT INTO `contract` VALUES (12, '3200', '居住', '2025-05-08 16:00:00', '2025-05-29 16:00:00', '张先生', NULL, '13800001234', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-29 00:00:00', NULL);
INSERT INTO `contract` VALUES (13, '3200', '居住', '2025-05-09 16:00:00', '2025-05-23 16:00:00', '刘先生', NULL, '13612340005', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-30 00:00:00', NULL);
INSERT INTO `contract` VALUES (14, '3200', '居住', '2025-06-30 16:00:00', '2025-07-30 16:00:00', '陈先生', NULL, '18712340025', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-31 00:00:00', NULL);
INSERT INTO `contract` VALUES (15, '3200', '居住', '2025-06-30 16:00:00', '2025-07-30 16:00:00', '陈先生', NULL, '18712340025', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-31 00:00:00', NULL);
INSERT INTO `contract` VALUES (16, '3200', '居住', '2025-06-30 16:00:00', '2025-07-30 16:00:00', '陈先生', NULL, '18712340025', '', NULL, '', '叁仟贰佰零拾零元整', '2025-05-31 00:00:00', NULL);
INSERT INTO `contract` VALUES (27, '3200', '仓储', '2025-04-30 16:00:00', '2025-12-10 16:00:00', '赵租房', 25, '13212340009', 'Ylfmoonn', NULL, '', '叁仟贰佰零拾零元整', '2025-05-31 00:00:00', 25);
INSERT INTO `contract` VALUES (28, '3200', '办公', '2025-05-01 16:00:00', '2025-08-08 16:00:00', '杨公寓', 43, '18912340027', 'Ylfmoonn', NULL, '', '叁仟贰佰零拾零元整', '2025-05-31 00:00:00', 43);
INSERT INTO `contract` VALUES (29, '3200', '居住', '2025-02-28 16:00:00', '2025-04-30 16:00:00', '穗露公寓', 34, '15912340018', 'Ylfmoonn', NULL, '', '叁仟贰佰零拾零元整', '2025-05-31 00:00:00', 34);
INSERT INTO `contract` VALUES (30, '3200', '办公', '2025-05-31 16:00:00', '2025-06-29 16:00:00', '张先生', 37, '13800001234', 'Ylfmoonn', NULL, '', '叁仟贰佰零拾零元整', '2025-06-20 00:00:00', 1);
INSERT INTO `contract` VALUES (41, '1220', '居住', '2026-04-30 16:00:00', '2026-05-30 16:00:00', '湘江悦家', 44, '19012340028', 'luyue', NULL, '', '壹仟贰佰贰拾零元整', '2026-04-30 00:00:00', 44);
INSERT INTO `contract` VALUES (42, '2208', '办公', '2026-04-30 16:00:00', '2026-05-30 16:00:00', '华佑e家', 46, '19212340030', 'luyue', NULL, '', '贰仟贰佰零拾捌元整', '2026-04-30 00:00:00', 46);
INSERT INTO `contract` VALUES (43, '1900', '居住', '2026-04-30 16:00:00', '2026-05-30 16:00:00', '房东直租', 5, '18800000005', 'luyue', NULL, '', '壹仟玖佰零拾零元整', '2026-04-30 00:00:00', 5);
INSERT INTO `contract` VALUES (44, '1600', '办公', '2026-05-02 16:00:00', '2026-05-15 16:00:00', '张先生', 1, '13800001234', 'luyue', NULL, '', '壹仟陆佰零拾零元整', '2026-04-30 00:00:00', 1);
INSERT INTO `contract` VALUES (45, '1450', '居住', '2026-04-30 16:00:00', '2026-05-30 16:00:00', '包租婆HOUSE', 24, '13312340008', 'luyue', NULL, '', '壹仟肆佰伍拾零元整', '2026-04-30 00:00:00', 24);
INSERT INTO `contract` VALUES (46, '3000', '居住', '2026-05-02 16:00:00', '2026-05-30 16:00:00', '杨公寓', 43, '18912340027', 'Lappand', NULL, '', '叁仟零佰零拾零元整', '2026-05-02 00:00:00', 43);
INSERT INTO `contract` VALUES (47, '3000', '居住', '2026-05-02 16:00:00', '2026-06-26 16:00:00', '杨公寓', 43, '18912340027', 'luyue', NULL, '', '叁仟零佰零拾零元整', '2026-05-02 00:00:00', 43);
INSERT INTO `contract` VALUES (48, '1950', '居住', '2026-04-30 16:00:00', '2026-06-26 16:00:00', '吴先生', 27, '15112340011', 'luyue', NULL, '', '壹仟玖佰伍拾零元整', '2026-05-02 00:00:00', 27);
INSERT INTO `contract` VALUES (49, '1300', '居住', '2026-05-08 16:00:00', '2026-05-29 16:00:00', '赵先生', 45, '19112340029', 'Lappand', NULL, '', '壹仟叁佰零拾零元整', '2026-05-08 00:00:00', 45);
INSERT INTO `contract` VALUES (50, '800', '仓储', '2026-05-09 16:00:00', '2026-05-27 16:00:00', '张先生', 51, '13630278915', 'luyue', NULL, '', '捌佰零拾零元整', '2026-05-09 00:00:00', 51);
INSERT INTO `contract` VALUES (51, '1900', '居住', '2026-05-09 16:00:00', '2026-05-29 16:00:00', '房东直租', 5, '18800000005', 'luyue', NULL, '', '壹仟玖佰零拾零元整', '2026-05-09 00:00:00', 5);
INSERT INTO `contract` VALUES (52, '1900', '居住', '2026-05-09 16:00:00', '2026-05-26 16:00:00', '房东直租', 5, '18800000005', 'luyue', NULL, '', '壹仟玖佰零拾零元整', '2026-05-09 00:00:00', 5);
INSERT INTO `contract` VALUES (53, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_c52183', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (54, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_e750af', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (55, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_cd0404', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (56, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_b0785c', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (57, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_e6b066', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (58, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_c8ee71', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (59, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_95d716', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (60, '5000', '办公', '2025-08-01 00:00:00', '2026-07-31 00:00:00', '测试房东', 1, '13800001111', 'tenant_1a76bc', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (61, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_d8c440', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (62, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_cb641e', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (63, '5000', '办公', '2025-08-01 00:00:00', '2026-07-31 00:00:00', '测试房东', 1, '13800001111', 'tenant_de8918', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (64, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_48a417', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (65, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_849f0d', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (66, '5000', '办公', '2025-08-01 00:00:00', '2026-07-31 00:00:00', '测试房东', 1, '13800001111', 'tenant_9b7c20', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (67, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_bd21c6', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (68, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_6c575f', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (69, '5000', '办公', '2025-08-01 00:00:00', '2026-07-31 00:00:00', '测试房东', 1, '13800001111', 'tenant_e9f585', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (70, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_4e07f2', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (71, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_ed9b4e', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (72, '5000', '办公', '2025-08-01 00:00:00', '2026-07-31 00:00:00', '测试房东', 1, '13800001111', 'tenant_be8486', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', 1);
INSERT INTO `contract` VALUES (73, '3000', '住宅', '2025-07-01 00:00:00', '2026-06-30 00:00:00', '测试房东', 1, '13800001111', 'tenant_d785e6', 1, '13900001111', '3000元/月', '2025-06-15 00:00:00', NULL);
INSERT INTO `contract` VALUES (74, '1950', '居住', '2026-05-12 16:00:00', '2026-05-30 16:00:00', '吴先生', 27, '15112340011', 'luyue', NULL, '', '壹仟玖佰伍拾零元整', '2026-05-11 00:00:00', 27);

-- ----------------------------
-- Table structure for house_detail
-- ----------------------------
DROP TABLE IF EXISTS `house_detail`;
CREATE TABLE `house_detail`  (
  `detail_id` int NOT NULL AUTO_INCREMENT COMMENT '详情表主键ID',
  `house_info_id` int UNSIGNED NOT NULL COMMENT '关联的 house_info 表主键ID',
  `photos` json NULL COMMENT '房源详情图片URL列表 (JSON格式, 例如: [\"url1.jpg\", \"url2.png\"])',
  `facilities` json NULL COMMENT '配套设施 (JSON格式, 例如: {\"wifi\": true, \"tv\": true, \"washer\": \"洗衣机\"})',
  `map_coordinates` json NULL COMMENT '地图坐标 (JSON格式, 例如: {\"latitude\": 30.123456, \"longitude\": 120.654321, \"address\": \"详细地址\"})',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`detail_id`) USING BTREE,
  UNIQUE INDEX `house_info_id`(`house_info_id` ASC) USING BTREE,
  CONSTRAINT `fk_house_detail_to_house_info` FOREIGN KEY (`house_info_id`) REFERENCES `house_info` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 25 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '房源详细信息表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of house_detail
-- ----------------------------
INSERT INTO `house_detail` VALUES (1, 1, '[\"https://images.unsplash.com/photo-1506744038136-46273834b3fb\", \"https://images.unsplash.com/photo-1494526585095-c41746248156\", \"https://images.unsplash.com/photo-1470770841072-f978cf4d019e\"]', '{\"tv\": true, \"wifi\": true, \"washer\": \"洗衣机\"}', '222', '2025-05-22 21:32:16', '2025-05-22 21:34:28');
INSERT INTO `house_detail` VALUES (2, 2, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', '{\"tv\": true, \"wifi\": true, \"washer\": true}', '222', '2025-05-22 23:37:15', '2025-05-22 23:37:33');
INSERT INTO `house_detail` VALUES (3, 47, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', '{\"tv\": true, \"bed\": true, \"wifi\": true, \"washer\": true, \"heating\": false, \"wardrobe\": true, \"naturalgas\": false, \"waterheater\": false, \"refrigerator\": true, \"airconditioner\": false}', '{\"lat\": 30, \"lng\": 120}', '2025-06-20 23:33:56', '2025-06-20 23:55:39');
INSERT INTO `house_detail` VALUES (4, 48, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg\"]', '{\"tv\": true, \"bed\": true, \"wifi\": true, \"washer\": true, \"heating\": false, \"wardrobe\": true, \"naturalgas\": false, \"waterheater\": true, \"refrigerator\": false, \"airconditioner\": false}', '{\"lat\": 30, \"lng\": 120}', '2025-06-20 23:36:54', '2025-06-20 23:56:33');
INSERT INTO `house_detail` VALUES (5, 49, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg\"]', '{\"tv\": false, \"bed\": true, \"wifi\": true, \"washer\": true, \"heating\": false, \"wardrobe\": false, \"naturalgas\": false, \"waterheater\": false, \"refrigerator\": false, \"airconditioner\": false}', '{\"lat\": 30, \"lng\": 120}', '2025-06-20 23:39:33', '2025-06-20 23:56:48');
INSERT INTO `house_detail` VALUES (6, 50, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg\"]', '{\"tv\": true, \"bed\": true, \"wifi\": true, \"washer\": false, \"heating\": false, \"wardrobe\": false, \"naturalgas\": false, \"waterheater\": false, \"refrigerator\": false, \"airconditioner\": false}', '{\"lat\": 30, \"lng\": 120}', '2025-06-20 23:41:38', '2025-06-20 23:56:56');
INSERT INTO `house_detail` VALUES (7, 51, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg\"]', '{\"tv\": true, \"bed\": true, \"wifi\": true, \"washer\": false, \"heating\": false, \"wardrobe\": false, \"naturalgas\": false, \"waterheater\": false, \"refrigerator\": true, \"airconditioner\": false}', '{\"lat\": 30, \"lng\": 120}', '2025-06-20 23:43:08', '2025-06-20 23:57:09');
INSERT INTO `house_detail` VALUES (12, 22, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg\"]', '{\"tv\": true, \"wifi\": true, \"washer\": true}', '222', '2025-06-21 00:00:58', '2025-06-21 00:35:52');
INSERT INTO `house_detail` VALUES (13, 34, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', NULL, NULL, '2025-06-21 00:02:03', '2025-06-21 00:35:55');
INSERT INTO `house_detail` VALUES (14, 43, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', NULL, NULL, '2025-06-21 00:02:55', '2025-06-21 00:36:16');
INSERT INTO `house_detail` VALUES (15, 46, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', NULL, NULL, '2025-06-21 00:03:40', '2025-06-21 00:03:40');
INSERT INTO `house_detail` VALUES (16, 27, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', '{\"tv\": true, \"wifi\": true, \"washer\": true}', '222', '2025-06-21 00:03:46', '2025-06-21 00:09:36');
INSERT INTO `house_detail` VALUES (17, 25, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', '{\"tv\": true, \"bed\": true, \"wifi\": true, \"washer\": false, \"heating\": false, \"wardrobe\": false, \"naturalgas\": false, \"waterheater\": false, \"refrigerator\": true, \"airconditioner\": false}', '{\"lat\": 30, \"lng\": 120}', '2025-06-21 00:03:51', '2025-06-21 00:36:24');
INSERT INTO `house_detail` VALUES (18, 21, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\"]', NULL, NULL, '2025-06-21 00:35:14', '2025-06-21 00:36:20');
INSERT INTO `house_detail` VALUES (19, 45, '[\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/4/a1e68eda3df44341b55a3beea55dda84.png\", \"https://i.pinimg.com/736x/f4/2c/7b/f42c7b16d92dab70ff7af2b59d02fdb5.jpg\", \"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg\"]', NULL, NULL, '2025-06-21 01:39:18', '2025-06-21 01:39:59');

-- ----------------------------
-- Table structure for house_info
-- ----------------------------
DROP TABLE IF EXISTS `house_info`;
CREATE TABLE `house_info`  (
  `id` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '标题，如：整租·锦源小区 2室1厅 南',
  `region` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '区，如：雨花',
  `block` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '街道，如：树木岭',
  `community` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '小区，如：锦源小区',
  `area` float NULL DEFAULT NULL COMMENT '面积，单位㎡',
  `direction` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '朝向，如：南',
  `rooms` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '几室几厅，如：2室1厅1卫',
  `price` int NULL DEFAULT NULL COMMENT '价格，单位：元/月',
  `rent_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '租赁方式，如：整租、合租',
  `decoration` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '装修情况，如：精装',
  `subway` tinyint(1) NULL DEFAULT 0 COMMENT '是否近地铁',
  `available` tinyint(1) NULL DEFAULT 1 COMMENT '是否随时看房',
  `tag_new` tinyint(1) NULL DEFAULT 0 COMMENT '是否新上',
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '房源图片',
  `publish_time` date NULL DEFAULT NULL COMMENT '发布时间，如：2天前',
  `page_views` int NULL DEFAULT NULL COMMENT '浏览量',
  `landlord` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '房东',
  `phone_num` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '房东电话',
  `house_num` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '房源编号',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_house_publish_id`(`publish_time` DESC, `id` DESC) USING BTREE,
  INDEX `idx_house_price`(`price` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 110 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of house_info
-- ----------------------------
INSERT INTO `house_info` VALUES (1, '整租·锦源小区 2室1厅 南', '雨花', '树木岭', '锦源小区', 73, '南', '2室1厅1卫', 1600, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg', '2025-05-15', 141, '张先生', '13800001234', '10001');
INSERT INTO `house_info` VALUES (2, '合租·泰时新雅园 4居室 南卧', '芙蓉', '晚报', '泰时新雅园', 18, '南', '4室2厅2卫', 580, '合租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-14', 903, '龟壳公寓', '13800005678', '10002');
INSERT INTO `house_info` VALUES (3, '整租·星宇V立方 1室0厅 南', '天心', '金盆岭', '星宇V立方', 29.14, '南', '1室0厅1卫', 1280, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-15', 72, '李女士', '13800007890', '10003');
INSERT INTO `house_info` VALUES (4, '合租·长远华樟名府 5居室 南卧', '雨花', '尚东', '长远华樟名府', 25, '南', '5室1厅3卫', 540, '合租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/385216b3a0474b7d98cfa5f367a11019.jpg', '2025-05-14', 61, '包租婆宿懒公寓', '13800009876', '10004');
INSERT INTO `house_info` VALUES (5, '整租·长大彩虹都 3室2厅 南/北', '天心', '铁道学院', '长大彩虹都', 90, '南/北', '3室2厅1卫', 1900, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-17', 2, '房东直租', '18800000005', '10005');
INSERT INTO `house_info` VALUES (6, '合租·山水华景 5居室 南卧', '芙蓉', '马王堆', '山水华景', 25, '南', '5室1厅2卫', 849, '合租', '精装', 0, 1, 0, 'https://ke-image.ljcdn.com/wanjia/885e92fd2470add49f2c29ce7824562c-1743474437330/458004f9fa46b67b17d8e69c543c97e5.jpg.250x182.jpg', '2025-05-15', 0, '长沙鸿威公寓', '18800000006', '10006');
INSERT INTO `house_info` VALUES (7, '整租·国税局 3室2厅 南', '天心', '书院路', '国税局', 120, '南', '3室2厅2卫', 2600, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/ae23849ba7a744c698e2a72301d01ec6.jpg', '2025-05-17', 0, '房东直租', '18800000007', '10007');
INSERT INTO `house_info` VALUES (8, '合租·运通尊苑 5居室 南卧', '芙蓉', '马王堆', '运通尊苑', 22, '南', '5室1厅2卫', 499, '合租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-15', 0, '长沙鸿威公寓', '18800000008', '10008');
INSERT INTO `house_info` VALUES (17, '整租·星城国际 2室1厅 南', '长沙县', '泉塘', '星城国际', 94, '南', '2室1厅', 1300, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-18', 345, '李公寓', '13812340001', '2034863457987198976');
INSERT INTO `house_info` VALUES (18, '独栋·冠寓 长沙大王山二店 端午节假特惠长租首月温馨单间/无中介/押一付一/学生特惠/拎包入住 1室1厅', NULL, NULL, NULL, 25, NULL, '1室1厅', 1082, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-07', 762, '冠寓', '15012340002', '81148');
INSERT INTO `house_info` VALUES (19, '整租·星语林名园 4室2厅 南/北', '雨花', '铁道学院', '星语林名园', 161, '南/北', '4室2厅', 2400, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg', '2025-05-18', 190, '张先生', '13912340003', '2034860054812819456');
INSERT INTO `house_info` VALUES (20, '独栋·长鸿公寓 袁家岭火车站店 袁家岭 火车站 精装公寓 （不短租） 1室1厅', NULL, NULL, NULL, 30, NULL, '1室1厅', 1280, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/87daa810e2264c8b978dca2250f3f0f2.jpg', '2025-05-09', 488, '长鸿公寓', '13712340004', '70636');
INSERT INTO `house_info` VALUES (21, '整租·2076至高点 1室1厅 东', '雨花', '左家塘', '2076至高点', 41, '东', '1室1厅', 1100, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/385216b3a0474b7d98cfa5f367a11019.jpg', '2025-05-19', 984, '刘先生', '13612340005', '2024412686569177088');
INSERT INTO `house_info` VALUES (22, '独栋·原宿奢宅 北辰定江洋 定江洋2-2007 3室2厅', NULL, NULL, NULL, 200, NULL, '3室2厅', 15800, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-16', 1507, '原宿奢宅', '13512340006', '92368');
INSERT INTO `house_info` VALUES (23, '整租·中海阅溪府 3室2厅 南', '岳麓', '东方红', '中海阅溪府', 112, '南', '3室2厅', 3200, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-18', 622, '杨女士', '13412340007', '2034617752949358592');
INSERT INTO `house_info` VALUES (24, '独栋·包租婆HOUSE 名富公寓 无中介 开福寺地铁口 华创 湘雅附一 名富公寓 押一付一 1室1厅', NULL, NULL, NULL, 33, NULL, '1室1厅', 1450, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/ae23849ba7a744c698e2a72301d01ec6.jpg', '2025-05-14', 882, '包租婆HOUSE', '13312340008', '91901');
INSERT INTO `house_info` VALUES (25, '整租·黄金一区 1室1厅 南', '望城', '望城区', '黄金一区', 47, '南', '1室1厅', 1100, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/16cc4d88c84d4a18b6b18e8a56a1460e.jpg', '2025-05-19', 208, '赵租房', '13212340009', '2033823854522007552');
INSERT INTO `house_info` VALUES (26, '独栋·包租婆宿懒公寓 保利天禧 不短租 无中介可月付 六沟垅地铁万达广场 山姆超市 1室1厅', NULL, NULL, NULL, 35, NULL, '1室1厅', 1801, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-17', 1131, '包租婆宿懒公寓', '13112340010', '89307');
INSERT INTO `house_info` VALUES (27, '整租·楚天世纪城 3室2厅 南', '长沙县', '泉塘', '楚天世纪城', 92, '南', '3室2厅', 1950, '整租', '精装', 0, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-19', 456, '吴先生', '15112340011', '2025545561456771072');
INSERT INTO `house_info` VALUES (28, '独栋·包租婆宿懒公寓 保利天禧 一线江景 不短租 近六沟垅地铁 山姆超市 万象城 可月付无中介 2室1厅', NULL, NULL, NULL, 38, NULL, '2室1厅', 2750, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-17', 1307, '包租婆宿懒公寓', '15212340012', '89307');
INSERT INTO `house_info` VALUES (29, '整租·泊富骊庭 3室1厅 南', '天心', '铁道学院', '泊富骊庭', 95, '南', '3室1厅', 2400, '整租', '精装', 0, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-18', 693, '周公寓', '15312340013', '2010950629303779328');
INSERT INTO `house_info` VALUES (30, '独栋·穗露公寓 湘江悦城 无中介费 湘江悦城精装四房 全长沙整租房源 4室2厅', NULL, NULL, NULL, 140, NULL, '4室2厅', 3000, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/385216b3a0474b7d98cfa5f367a11019.jpg', '2025-05-13', 1008, '穗露公寓', '15512340014', '70270');
INSERT INTO `house_info` VALUES (31, '整租·尚鑫海悦 1室0厅 南/北', '长沙县', '开元路', '尚鑫海悦', 28, '南/北', '1室0厅', 1200, '整租', '简装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-18', 312, '丁先生', '15612340015', '1936725279640649728');
INSERT INTO `house_info` VALUES (32, '整租·润和湘江天地 1室1厅 南', '望城', '金星北', '润和湘江天地', 109, '南', '1室1厅', 1500, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg', '2025-05-19', 565, '孙女士', '15712340016', '2004420834805940224');
INSERT INTO `house_info` VALUES (33, '整租·公交金盆小区 2室2厅 南', '天心', '金盆岭', '公交金盆小区', 70, '南', '2室2厅', 1560, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-14', 788, '朱公寓', '15812340017', '2028676655848882176');
INSERT INTO `house_info` VALUES (34, '独栋·穗露公寓 润和天地印湘江 整租 越秀湘江星汇城豪装大平层 全长沙都有房源 4室2厅', NULL, NULL, NULL, 186, NULL, '4室2厅', 6600, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/385216b3a0474b7d98cfa5f367a11019.jpg', '2025-05-18', 1406, '穗露公寓', '15912340018', '53017');
INSERT INTO `house_info` VALUES (35, '整租·旺德府恺悦国际 3室2厅 东', '长沙县', '月湖', '旺德府恺悦国际', 99, '东', '3室2厅', 2200, '整租', '精装', 0, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-17', 821, '何之家', '18012340019', '1982314656307347456');
INSERT INTO `house_info` VALUES (36, '整租·桂芳家园 3室2厅 东南', '望城', '望城区', '桂芳家园', 110, '东南', '3室2厅', 1600, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/87daa810e2264c8b978dca2250f3f0f2.jpg', '2025-05-16', 670, '王先生', '18112340020', '2033406282563584000');
INSERT INTO `house_info` VALUES (37, '整租·世锦家和院 3室2厅 南', '长沙县', '开元路', '世锦家和院', 80, '南', '3室2厅', 1800, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/16cc4d88c84d4a18b6b18e8a56a1460e.jpg', '2025-05-17', 907, '张女士', '18212340021', '2034515051976589312');
INSERT INTO `house_info` VALUES (38, '合租·保利麓谷林语D区 4居室 南卧', '岳麓', '麓谷西', '保利麓谷林语D区', 28, '南卧', '4居室', 799, '合租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/ae23849ba7a744c698e2a72301d01ec6.jpg', '2025-05-18', 456, '美美公寓', '18312340022', '2034904158825349120');
INSERT INTO `house_info` VALUES (39, '整租·名都花园 3室2厅 南', '雨花', '赤岗冲', '名都花园', 141, '南', '3室2厅', 2700, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-17', 1029, '刘公寓', '18512340023', '2032671830451421184');
INSERT INTO `house_info` VALUES (40, '合租·博林金谷 4居室 南卧', '天心', '新开铺', '博林金谷', 28, '南卧', '4居室', 1150, '合租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-16', 723, '快聚租公寓', '18612340024', '2026514311534346240');
INSERT INTO `house_info` VALUES (41, '整租·碧桂园翘楚棠 4室2厅 南', '长沙县', '万家丽北', '碧桂园翘楚棠', 138.9, '南', '4室2厅', 2750, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg', '2025-05-19', 1009, '陈先生', '18712340025', '2009581722345144320');
INSERT INTO `house_info` VALUES (42, '合租·东方新城 5居室 南卧', '芙蓉', '德政园', '东方新城', 18, '南卧', '5居室', 599, '合租', '毛坯', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-19', 305, '长沙鸿威公寓', '18812340026', '2004451401635201024');
INSERT INTO `house_info` VALUES (43, '整租·北辰中央公园(慧辰园) 2室2厅 南', '天心', '省政府', '北辰中央公园(慧辰园)', 95, '南', '2室2厅', 3000, '整租', '精装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-19', 1213, '杨公寓', '18912340027', '2010951165017063424');
INSERT INTO `house_info` VALUES (44, '独栋·湘江悦家 麓隐桐溪·大王山店 3号线大王山正地铁口/开业特惠95折/无中介/无服务费A 开间', NULL, NULL, NULL, 37.28, NULL, '1室0厅1卫', 1220, '整租', '精装', 1, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/16cc4d88c84d4a18b6b18e8a56a1460e.jpg', '2025-05-01', 806, '湘江悦家', '19012340028', '84585');
INSERT INTO `house_info` VALUES (45, '整租·融城花苑 3室2厅 南', '雨花', '井湾子', '融城花苑', 99, '南', '3室2厅', 1300, '整租', '精装', 0, 1, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-19', 523, '赵先生', '19112340029', '1884114366576459776');
INSERT INTO `house_info` VALUES (46, '独栋·华佑e家 万国城店 无中介费可月付 润和珠江星环马厂地铁站 万国城两室 2室2厅', NULL, NULL, '楚天世纪城', 76, NULL, '2室2厅', 2208, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-19', 1178, '华佑e家', '19212340030', '92145');
INSERT INTO `house_info` VALUES (47, '整租·九龙小区 3室1厅 北', '雨花', '树木岭', '九龙小区', 73, '北', '2室1厅1卫', 1800, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/50f1f56b2b5c41d18dc84fe8dc2be595.jpg', '2025-05-15', 1, '张先生', '13630278915', '10001');
INSERT INTO `house_info` VALUES (48, '合租·盘锦小区 2室1厅 南', '岳麓', '德政园', '盘锦小区', 83, '南', '2室1厅1卫', 2000, '整租', '简装', 0, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/8bdaf9c736aa47a49bf70669672566f6.jpg', '2025-05-15', 1, '张先生', '13630278915', '10001');
INSERT INTO `house_info` VALUES (49, '整租·黄金一区 3室2厅 北', '天心', '泉塘', '黄金一区', 103, '北', '2室1厅1卫', 2400, '整租', '精装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/1e7e4c632f5948dd95829709a06a904e.jpg', '2025-05-15', NULL, '张先生', '13630278915', '10001');
INSERT INTO `house_info` VALUES (50, '整租·桃花村 3室1厅 南北', '岳麓', '桃花村', '桃花村', 62, '南北', '2室1厅1卫', 1000, '整租', '简装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/385216b3a0474b7d98cfa5f367a11019.jpg', '2025-05-15', NULL, '张先生', '13630278915', '10001');
INSERT INTO `house_info` VALUES (51, '整租·锦源小区 1室1厅 东西', '芙蓉', '树木岭', '锦源小区', 50, '东西', '2室1厅1卫', 800, '整租', '简装', 1, 1, 1, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/property_detail_pending/0e54185af1744ef0ab60029cb130b32c.jpg', '2025-05-15', 2, '张先生', '13630278915', '10001');

-- ----------------------------
-- Table structure for log_entries
-- ----------------------------
DROP TABLE IF EXISTS `log_entries`;
CREATE TABLE `log_entries`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NULL DEFAULT NULL,
  `level` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `module` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `func_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `line_no` int NULL DEFAULT NULL,
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `traceback` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 199698 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of log_entries
-- ----------------------------

-- ----------------------------
-- Table structure for message
-- ----------------------------
DROP TABLE IF EXISTS `message`;
CREATE TABLE `message`  (
  `message_id` int NOT NULL AUTO_INCREMENT,
  `content` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '消息内容',
  `sender_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '发送者用户名',
  `receiver_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '接收者用户名',
  `timestamp` datetime NULL DEFAULT NULL COMMENT '消息时间戳',
  `channel_id` int NULL DEFAULT NULL,
  PRIMARY KEY (`message_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 51 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of message
-- ----------------------------
INSERT INTO `message` VALUES (1, 'manba out', 'Andy', 'LU', '2025-05-19 16:08:26', 1);
INSERT INTO `message` VALUES (2, 'what can i say', 'Andy', 'LU', '2025-05-19 16:10:02', 1);
INSERT INTO `message` VALUES (3, 'kobe brant', 'Andy', 'LU', '2025-05-19 16:35:40', 1);
INSERT INTO `message` VALUES (4, 'man', 'Andy', 'LU', '2025-05-19 16:43:08', 1);
INSERT INTO `message` VALUES (5, 'hahahaha', 'Andy', 'LU', '2025-05-19 16:43:08', 1);
INSERT INTO `message` VALUES (6, 'hahahahahaha', 'Andy', 'LU', '2025-05-21 16:29:32', 1);
INSERT INTO `message` VALUES (7, 'manba in', 'Andy', 'LU', '2025-05-21 19:08:20', 1);
INSERT INTO `message` VALUES (8, 'manba out', 'Andy', 'LU', '2025-05-21 19:08:20', 1);
INSERT INTO `message` VALUES (9, '你是谁?', 'Andy', 'LU', '2025-05-21 19:08:20', 1);
INSERT INTO `message` VALUES (10, '我是乃龙', 'Andy', 'LU', '2025-05-21 19:15:39', 1);
INSERT INTO `message` VALUES (11, '我会喷火，你会吗', 'Andy', 'LU', '2025-05-21 19:56:29', 1);
INSERT INTO `message` VALUES (12, 'woc', 'Andy', 'LU', '2025-05-21 20:48:06', 1);
INSERT INTO `message` VALUES (13, 'bin', 'Andy', 'LU', '2025-05-21 21:01:37', 1);
INSERT INTO `message` VALUES (14, '你好', 'Andy', 'LU', '2025-05-23 22:42:10', 1);
INSERT INTO `message` VALUES (15, '鸣潮启动', '赵先生', 'Ylfmoonn', '2025-06-01 14:31:33', 1);
INSERT INTO `message` VALUES (16, '我想租房', 'Ylfmoonn', '赵先生', '2025-06-02 14:30:27', 2);
INSERT INTO `message` VALUES (17, 'hello', 'Lappand', 'Ylfmoonn', '2025-06-08 22:42:26', 3);
INSERT INTO `message` VALUES (21, '你好', 'Ylfmoonn', 'Lappand', '2025-06-08 22:53:59', 3);
INSERT INTO `message` VALUES (22, '你叫什么名字', 'Lappand', 'Ylfmoonn', '2025-06-08 23:00:19', 3);
INSERT INTO `message` VALUES (23, 'hi', 'aaaa', '房东', '2025-06-12 19:31:50', 4);
INSERT INTO `message` VALUES (24, '你好', 'aaaa', '华佑e家', '2025-06-12 19:32:12', 5);
INSERT INTO `message` VALUES (25, 'aaa', 'aaaa', '华佑e家', '2025-06-12 19:39:01', 5);
INSERT INTO `message` VALUES (26, 'ヾ(￣▽￣)Bye~Bye~', '华佑e家', 'aaaa', '2025-06-12 19:39:45', 5);
INSERT INTO `message` VALUES (27, '你头像无了', 'aaaa', '华佑e家', '2025-06-12 20:04:48', 5);
INSERT INTO `message` VALUES (29, '你好，我是lap', 'Lappand', 'luyue', '2026-04-30 15:02:09', 6);
INSERT INTO `message` VALUES (30, '你好，我是陆岳', 'luyue', 'Lappand', '2026-04-30 15:02:28', 6);
INSERT INTO `message` VALUES (31, '你好，请问你知道agent吗', 'Lappand', 'luyue', '2026-04-30 15:22:39', 6);
INSERT INTO `message` VALUES (32, '我了解一点，怎么了？', 'luyue', 'Lappand', '2026-04-30 15:22:53', 6);
INSERT INTO `message` VALUES (33, '我想学习相关方面的内容', 'Lappand', 'luyue', '2026-05-02 14:56:42', 6);
INSERT INTO `message` VALUES (34, '你能教我吗', 'Lappand', 'luyue', '2026-05-02 14:56:45', 6);
INSERT INTO `message` VALUES (35, '好的', 'luyue', 'Lappand', '2026-05-02 14:56:49', 6);
INSERT INTO `message` VALUES (36, 'API 测试消息', 'auto_test_user', 'test_receiver', '2026-05-11 15:42:16', 9);
INSERT INTO `message` VALUES (37, 'API 测试消息', 'auto_test_user', 'test_receiver', '2026-05-11 15:43:51', 9);
INSERT INTO `message` VALUES (38, 'API 测试消息', 'auto_test_user', 'test_receiver', '2026-05-11 15:48:33', 9);
INSERT INTO `message` VALUES (39, 'API 测试消息', 'auto_test_user', 'test_receiver', '2026-05-11 15:50:07', 9);
INSERT INTO `message` VALUES (40, 'API 测试消息', 'auto_test_user', 'test_receiver', '2026-05-11 15:51:43', 9);
INSERT INTO `message` VALUES (41, 'API 测试消息 a10a4a', 'auto_test_user', 'test_receiver', '2026-05-11 16:12:51', 9);
INSERT INTO `message` VALUES (42, '', 'auto_test_user', 'test_receiver', '2026-05-11 16:12:51', 9);
INSERT INTO `message` VALUES (43, 'API 测试消息 28b91b', 'auto_test_user', 'test_receiver', '2026-05-11 16:15:19', 9);
INSERT INTO `message` VALUES (44, '', 'auto_test_user', 'test_receiver', '2026-05-11 16:15:19', 9);
INSERT INTO `message` VALUES (45, 'API 测试消息 03e885', 'auto_test_user', 'test_receiver', '2026-05-11 16:16:53', 9);
INSERT INTO `message` VALUES (46, '', 'auto_test_user', 'test_receiver', '2026-05-11 16:16:53', 9);
INSERT INTO `message` VALUES (47, 'API 测试消息 3f517e', 'auto_test_user', 'test_receiver', '2026-05-11 16:19:01', 9);
INSERT INTO `message` VALUES (48, '', 'auto_test_user', 'test_receiver', '2026-05-11 16:19:01', 9);
INSERT INTO `message` VALUES (49, 'API 测试消息 2719bc', 'auto_test_user', 'test_receiver', '2026-05-11 16:23:16', 9);
INSERT INTO `message` VALUES (50, '', 'auto_test_user', 'test_receiver', '2026-05-11 16:23:16', 9);

-- ----------------------------
-- Table structure for news
-- ----------------------------
DROP TABLE IF EXISTS `news`;
CREATE TABLE `news`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `publish_time` datetime NULL DEFAULT NULL,
  `author` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `coverImageUrl` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 79 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of news
-- ----------------------------
INSERT INTO `news` VALUES (29, '鹰角网络多项跨界合作引关注', '<h1>近日，知名游戏研发与发行公司鹰角网络正式宣布，旗下热门手游《明日方舟》将于 7 月开启名为 “夏日嘉年华・潮涌海滨” 的大型限时活动。此次活动不仅包含全新剧情章节、限定干员及皮肤上线，还将联动多家品牌开展跨界合作，引发玩家群体广泛关注。​</h1><p>据官方透露，“夏日嘉年华・潮涌海滨” 活动将带来超过 10 万字的全新剧情，玩家将跟随罗德岛干员们的脚步，探索神秘海滨城市的故事。同时，活动期间将推出 3 位限定六星干员与 5 款夏日主题皮肤，其中部分角色设定融入海洋元素，极具视觉冲击力。为提升玩家体验，鹰角网络还优化了活动界面交互系统，并新增多线程剧情选择功能，增强游戏代入感。​</p><p>在跨界合作领域，鹰角网络与国内知名运动品牌安踏达成合作，推出联名运动鞋系列，将《明日方舟》经典角色元素融入鞋款设计；与连锁咖啡品牌瑞幸合作推出主题饮品，消费者购买指定产品可获得游戏道具兑换码。此外，鹰角网络还计划在上海、广州等城市举办线下嘉年华活动，现场设置 AR 互动游戏、限定周边售卖等环节。​</p><p>自 2019 年上线以来，《明日方舟》凭借独特的塔防玩法与世界观设定，在全球范围内积累了超 3000 万注册用户。此次大型活动的推出，不仅展现了鹰角网络在游戏内容持续更新上的投入，更凸显其在 IP 衍生与跨界合作领域的战略布局。行业分析师指出，此类多维度的运营模式或将为国产二次元游戏商业化探索提供新范例。​</p><p>据悉，“夏日嘉年华・潮涌海滨” 活动具体上线时间及更多合作细节，将在鹰角网络后续发布的官方公告中揭晓。​</p><p><br></p><img src=\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/cc7e5b220ad948d6983ab23e1e85708f.jpg\"><p></p>', '2025-06-20 14:57:55', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/b49832b8b9134be48658e2ff0ab8539f.jpg');
INSERT INTO `news` VALUES (30, '中共中央政治局召开会议 分析研究当前经济形势和经济工作​', '<h1><strong>中共中央政治局召开会议 分析研究当前经济形势和经济工作​</strong></h1><p>​</p><p>4 月 25 日，中共中央政治局召开会议，对当前经济形势和经济工作展开深入分析研究，会议由中共中央总书记习近平主持。​</p><p>会议认为，今年以来，在以习近平同志为核心的党中央对经济工作的全面引领下，各地区各部门齐心协力攻坚克难，各项宏观政策协同发力，促使经济呈现向好发展态势，社会信心不断提振，高质量发展稳步推进，社会大局维持稳定。然而，我国经济持续回升向好的根基仍有待进一步稳固，同时外部冲击影响也在加大。在此情形下，必须强化底线思维，充分筹备预案，扎实推进经济工作。​</p><p>会议指出，要坚定不移地坚持稳中求进工作总基调，完整、准确、全面地贯彻新发展理念，加快构建新发展格局，统筹协调国内经济工作与国际经贸斗争，坚定不移地办好自身事务，坚定不移地扩大高水平对外开放，重点聚焦稳就业、稳企业、稳市场、稳预期，凭借高质量发展的确定性来应对外部环境急剧变化所带来的不确定性。​</p><p>会议着重强调，需加紧实施更为积极有为的宏观政策，充分运用好更加积极的财政政策以及适度宽松的货币政策。加快推进地方政府专项债券、超长期特别国债等的发行与使用，切实兜牢基层 “三保” 底线。适时进行降准降息操作，维持流动性充裕，加大力度支持实体经济。创设新的结构性货币政策工具，设立新型政策性金融工具，以此支持科技创新、扩大消费、稳定外贸等，强化政策取向的一致性。​</p><p>在促进消费方面，会议指出要提高中低收入群体收入，大力推动服务消费发展，增强消费对经济增长的拉动作用。尽快清理消费领域的限制性措施，设立服务消费与养老再贷款。加大资金支持力度，扩围提质实施 “两新” 政策，加力推进 “两重” 建设。​</p><p>对于企业帮扶，会议强调要通过多种举措助力困难企业。加强融资支持，加快推动内外贸一体化进程。培育壮大新质生产力，打造一批新兴支柱产业。持续发力推进关键核心技术攻关，创新推出债券市场的 “科技板”，加快实施 “人工智能 +” 行动。大力推动重点产业提质升级，坚持标准引领，规范市场竞争秩序。​</p><p>在改革开放层面，会议强调要秉持用深化改革开放的方式解决发展中问题的理念。加快全国统一大市场建设，扎实开展规范涉企执法专项行动。加大服务业开放试点政策力度，加强对企业 “走出去” 的服务支持。与国际社会携手，积极维护多边主义，坚决反对单边霸凌行径。​</p><p>在风险防范领域，会议指出要持续发力防范化解重点领域风险。继续实施地方政府一揽子化债政策，加快解决地方政府拖欠企业账款问题。加力实施城市更新行动，有力有序推进城中村和危旧房改造。加快构建房地产发展新模式，加大高品质住房供给，优化存量商品房收购政策，持续巩固房地产市场稳定态势。持续稳定和活跃资本市场。​</p><p>在保障民生方面，会议强调要着力保民生。对受关税影响较大的企业，提高失业保险基金稳岗返还比例。健全分层分类的社会救助体系。加强农业生产，稳定粮食等重要农产品价格。巩固拓展脱贫攻坚成果同乡村振兴有效衔接。持续抓好安全生产和防灾减灾等各项工作。​</p><p>此外，会议指出要不断完善稳就业稳经济的政策工具箱，既定政策尽早出台并尽快见效，根据形势变化及时推出增量储备政策，加强超常规逆周期调节，全力巩固经济发展和社会稳定的基本面。同时，要加强党对经济工作的全面领导，鼓励党员干部迎难而上、主动作为，树立和践行正确政绩观。认真开展深入贯彻中央八项规定精神学习教育，以作风建设新成效开创高质量发展新局面。会议还研究了其他事项。</p><p></p>', '2025-06-20 15:00:03', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/19591260d6f8473ca8b079e81b982d94.jpg');
INSERT INTO `news` VALUES (31, '中南大学科研攻关—我们走在前面', '<h1><strong>中南大学重大科研成果助力新能源材料领域突破 产学研深度融合再创新高​</strong></h1><p>近日，中南大学传来喜讯，由该校材料科学与工程学院牵头的科研团队在新能源材料领域取得重大突破，其研发的新型锂离子电池正极材料技术，成功实现能量密度提升 30%，循环寿命延长 50%，相关成果已发表于国际顶级学术期刊《自然・材料》，并同步申请多项国家发明专利。​</p><p>该项目团队历时五年攻关，通过对富锂锰基正极材料晶体结构的创新性设计，结合纳米级表面修饰技术，有效解决了传统材料存在的电压衰减快、热稳定性差等行业难题。“这项技术的突破，意味着未来电动汽车续航里程有望大幅提升，同时降低电池成本，对新能源汽车产业发展具有里程碑意义。” 项目负责人、中南大学特聘教授王某某在成果发布会上表示。​</p><p>作为国内顶尖综合性研究型大学，中南大学始终坚持 “四个面向” 战略导向，持续深化产学研用协同创新机制。此次成果转化已与国内头部新能源企业达成战略合作，计划年内建成中试生产线，预计三年内实现规模化应用，年产值有望突破 50 亿元。同时，中南大学依托该成果，联合共建 “新能源材料国家工程研究中心”，旨在打造集技术研发、人才培养、产业孵化于一体的创新平台。​</p><p>近年来，中南大学在科研创新领域成绩斐然。近三年承担国家级科研项目超 800 项，累计获得国家科技三大奖 12 项，多项成果在轨道交通、矿产资源开发等领域实现产业化应用。学校相关负责人介绍，未来将继续聚焦国家重大战略需求，强化基础研究与应用研究深度融合，为服务国家高水平科技自立自强贡献 “中南力量”。​</p><p>据悉，中南大学还将围绕该成果举办国际新能源材料学术论坛，邀请全球顶尖专家学者共商行业发展趋势，进一步提升中国在新能源材料领域的国际话语权。​</p><p><br></p><img src=\"http://y3.ifengimg.com/a/2015_52/577ffab39ca5256.jpg\"><p></p>', '2025-06-20 15:03:11', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/159ff02b374e4823937e7145e25ee848.jpg');
INSERT INTO `news` VALUES (32, '多地出台新政规范房屋租赁市场 重点整治 “高收低租” 乱象', '<h1>近日，北京、上海、广州等多个城市相继出台房屋租赁市场专项整治政策，旨在规范行业秩序，保障租客合法权益。新规明确要求租赁企业租金收支比不得超过 85%，严厉打击 “高收低租”“长收短付” 等违规经营行为。同时，建立租赁企业信用评价体系，对违规企业实施联合惩戒。相关部门表示，后续将开展为期三个月的专项检查行动，重点排查存在资金风险的租赁企业，从源头上防范 “爆雷” 隐患，为房屋租赁市场营造健康稳定的环境。</h1><img src=\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/cc7e5b220ad948d6983ab23e1e85708f.jpg\"><p></p>', '2025-06-20 15:04:52', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/49420d128b444767b206e68a1562f2d0.jpg');
INSERT INTO `news` VALUES (33, '房屋租赁市场迎来 “金三银四” 旺季 一线城市租金环比上涨 3%', '<h1><strong>房屋租赁市场迎来 “金三银四” 旺季 一线城市租金环比上涨 3%​</strong></h1><p>随着春季求职季的到来，房屋租赁市场热度持续攀升。据专业房产平台数据显示，今年 “金三银四” 期间，北京、上海、深圳等一线城市房屋租赁成交量环比增长 25%，平均租金较上月上涨 3%。其中，交通便利、配套完善的地铁沿线房源成为租客首选，一居室小户型房源供不应求。房产中介分析，受就业市场回暖影响，新毕业大学生及换岗求职者租赁需求集中释放，推动租金价格小幅上扬。同时，部分房东为吸引租客，推出免租期、赠送家电等优惠活动，市场呈现供需两旺态势。</p><p></p>', '2025-06-20 15:06:47', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/9e29ba8e5ee24521a98c05a6d9fb7009.jpg');
INSERT INTO `news` VALUES (34, '数字化赋能房屋租赁 线上 VR 看房成租客选房新趋势', '<h1><strong>数字化赋能房屋租赁 线上 VR 看房成租客选房新趋势​</strong></h1><p>随着科技的发展，数字化技术在房屋租赁领域的应用愈发广泛。多家房屋租赁平台加大 VR 技术投入，推出线上 VR 看房功能，让租客足不出户即可全方位查看房源细节。数据显示，使用 VR 看房功能的租客占比已从去年的 20% 提升至今年的 45%，且通过 VR 看房达成租赁交易的周期较传统方式缩短近一半。此外，平台还引入 AI 智能客服，实时解答租客疑问，优化租赁流程。房产行业专家表示，数字化手段的应用不仅提升了租客选房效率和体验，也推动房屋租赁行业向智能化、高效化方向发展。</p><img src=\"https://p2.ssl.qhimgs1.com/t01537706f492c7e8f2.jpg\">', '2025-06-20 15:07:44', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/04495e83075c4494be67481d2430af94.jpg');
INSERT INTO `news` VALUES (35, '乡村闲置房屋盘活计划启动 租赁市场开辟新蓝海', '<h1>为推动乡村振兴战略实施，多地政府联合房产企业启动乡村闲置房屋盘活计划，将农村空置住宅改造为特色民宿、创意工作室等租赁产品，乡村房屋租赁市场迎来发展新机遇。首批试点地区包括浙江莫干山、云南丽江等旅游资源丰富的村落，通过统一规划设计，既保留乡村建筑特色，又完善现代生活设施，吸引城市游客和创业者入驻。​</h1><p>某参与项目的房产企业负责人表示，改造后的乡村租赁房源，月租金较城市同类房源低 30% - 50%，且租期灵活，短租、长租均可。数据显示，部分试点村房屋出租率已超 70%，不仅增加了村民财产性收入，还带动了周边农产品销售和乡村旅游发展，形成乡村经济新增长点。</p><p></p>', '2025-06-20 15:09:04', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/5f20633c13e04bca8dc7ec7e89643c06.jpg');
INSERT INTO `news` VALUES (36, '老旧小区房屋改造升级 租赁性价比显著提升', '<h1><strong>老旧小区房屋改造升级 租赁性价比显著提升​</strong></h1><p>针对城市老旧小区房屋租赁市场需求，多地启动老旧小区改造工程，通过外立面修缮、加装电梯、优化户型等措施，提升老旧房源的居住品质和租赁性价比。改造后的老旧小区房屋，在保留地段优势的同时，居住环境大幅改善，吸引了大量年轻租客。​</p><p>以某二线城市为例，经过改造的老旧小区房屋，租金较改造前上涨 15% - 20%，但出租周期缩短近三分之二。房产中介表示，改造后的房源不仅基础设施更完善，还新增了智能门禁、社区共享空间等现代化设施，极大提升了租客的居住体验，有效激活了老旧小区房屋租赁市场活力。</p><img src=\"https://p0.ssl.qhimgs1.com/t017331d96c690babb6.jpg\">', '2025-06-20 15:09:58', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/8a1481ac92054fc4987e740151bd281b.jpg');
INSERT INTO `news` VALUES (38, '房屋租赁与社区服务深度融合 打造一站式生活圈', '<h1><strong>房屋租赁与社区服务深度融合 打造一站式生活圈​</strong></h1><p>为提升租客生活便利性，房屋租赁企业与社区服务机构展开深度合作，推出 “租赁 + 社区服务” 新模式。租客在租房的同时，可享受社区提供的家政保洁、健康管理、教育培训等一站式服务，部分服务还可通过租赁积分兑换。​</p><p>某长租公寓品牌与社区医院合作，为租客提供免费基础体检和健康咨询；与周边商超联动，推出专属购物优惠。这种模式不仅增强了租客的居住粘性，还带动了社区商业发展。社区工作人员表示，租赁与社区服务的融合，有助于构建和谐邻里关系，提升社区整体生活品质。</p><img src=\"https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/cc7e5b220ad948d6983ab23e1e85708f.jpg\"><p>某头部租赁平台数据显示，带有 “绿色租赁” 标识的房源浏览量比普通房源高 40%，签约率提升 25%。租客张女士表示：“虽然这类房源租金略高，但居住更健康舒适，长期来看也能节省生活成本。” 行业专家认为，“绿色租赁” 标准的推行，将推动房屋租赁行业向可持续方向转型，助力城市低碳发展。</p>', '2025-06-20 15:12:17', NULL, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/general_uploads/b9e674415ed1424795a6750df969c86d.jpg');

-- ----------------------------
-- Table structure for rental
-- ----------------------------
DROP TABLE IF EXISTS `rental`;
CREATE TABLE `rental`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `landlord_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `house_id` int NULL DEFAULT NULL,
  `currentDate` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 50 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rental
-- ----------------------------
INSERT INTO `rental` VALUES (10, 'Ylfmoonn', '赵租房', 25, '2025-05-31 00:00:00');
INSERT INTO `rental` VALUES (11, 'Ylfmoonn', '杨公寓', 43, '2025-05-31 00:00:00');
INSERT INTO `rental` VALUES (12, 'Ylfmoonn', '穗露公寓', 34, '2025-05-31 00:00:00');
INSERT INTO `rental` VALUES (13, 'Ylfmoonn', '张先生', 1, '2025-06-20 00:00:00');
INSERT INTO `rental` VALUES (14, 'Lappand', '赵先生', 45, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (15, 'Lappand', '陈先生', 41, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (16, 'luyue', '孙女士', 32, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (17, 'Ylfmoonn', '穗露公寓', 34, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (18, 'Lappand', '美美公寓', 38, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (19, 'Lappand', '刘先生', 21, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (20, 'luyue', '刘先生', 21, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (21, 'Lappand', '赵租房', 25, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (22, 'luyue', '赵租房', 25, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (23, 'luyue', '湘江悦家', 44, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (24, 'luyue', '华佑e家', 46, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (25, 'luyue', '房东直租', 5, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (26, 'luyue', '张先生', 1, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (27, 'luyue', '包租婆HOUSE', 24, '2026-04-30 00:00:00');
INSERT INTO `rental` VALUES (28, 'Lappand', '杨公寓', 43, '2026-05-02 00:00:00');
INSERT INTO `rental` VALUES (29, 'luyue', '杨公寓', 43, '2026-05-02 00:00:00');
INSERT INTO `rental` VALUES (30, 'luyue', '吴先生', 27, '2026-05-02 00:00:00');
INSERT INTO `rental` VALUES (31, 'Lappand', '赵先生', 45, '2026-05-08 00:00:00');
INSERT INTO `rental` VALUES (32, 'luyue', '张先生', 51, '2026-05-09 00:00:00');
INSERT INTO `rental` VALUES (33, 'luyue', '房东直租', 5, '2026-05-09 00:00:00');
INSERT INTO `rental` VALUES (34, 'luyue', '房东直租', 5, '2026-05-09 00:00:00');
INSERT INTO `rental` VALUES (35, 'tenant_cd0404', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (36, 'tenant_b0785c', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (37, 'tenant_e6b066', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (38, 'tenant_c8ee71', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (39, 'tenant_95d716', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (40, 'tenant_1a76bc', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (41, 'tenant_cb641e', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (42, 'tenant_de8918', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (43, 'tenant_849f0d', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (44, 'tenant_9b7c20', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (45, 'tenant_6c575f', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (46, 'tenant_e9f585', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (47, 'tenant_ed9b4e', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (48, 'tenant_be8486', '测试房东', 1, '2025-06-15 00:00:00');
INSERT INTO `rental` VALUES (49, 'luyue', '吴先生', 27, '2026-05-11 00:00:00');

-- ----------------------------
-- Table structure for repair_complaint
-- ----------------------------
DROP TABLE IF EXISTS `repair_complaint`;
CREATE TABLE `repair_complaint`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `report_reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `house_address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `repair_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `repair_description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `complaint_content` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `complaint_person` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `agreed_terms` int NULL DEFAULT NULL,
  `create_at` datetime NULL DEFAULT NULL,
  `handle` int NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 80 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of repair_complaint
-- ----------------------------
INSERT INTO `repair_complaint` VALUES (1, 'repair', 'dasdas', '水电维修', '', NULL, NULL, 1, '2025-05-19 10:50:31', NULL);
INSERT INTO `repair_complaint` VALUES (2, 'repair', 'dasdas', '水电维修', '', NULL, NULL, 1, '2025-05-19 10:56:48', NULL);
INSERT INTO `repair_complaint` VALUES (3, 'complaint', 'dasdas', '水电维修', '', NULL, '李茜', 1, '2025-05-19 10:58:03', NULL);
INSERT INTO `repair_complaint` VALUES (4, 'repair', 'aaaaaaa', '网络维修', '', '', NULL, 1, '2025-05-19 11:02:59', NULL);
INSERT INTO `repair_complaint` VALUES (5, 'repair', 'fffffffff', '其他维修', 'aaaaa', '', NULL, 1, '2025-05-19 11:05:07', NULL);
INSERT INTO `repair_complaint` VALUES (6, 'repair', '11111', '设备维修', '', '', NULL, 1, '2025-05-19 11:12:23', NULL);
INSERT INTO `repair_complaint` VALUES (7, 'repair', '12舍', '网络维修', '', '', '', 1, '2025-05-19 11:16:21', NULL);
INSERT INTO `repair_complaint` VALUES (8, 'complaint', '', NULL, '王万古', 'aaaaaaaaa', '王万古', 1, '2025-05-19 11:19:19', NULL);
INSERT INTO `repair_complaint` VALUES (9, 'repair', 'sssssssssssss', '网络维修', ' ', ' ', '', 1, '2025-05-19 11:20:25', NULL);
INSERT INTO `repair_complaint` VALUES (10, 'repair', 'sssssssssssss', '网络维修', ' ', ' ', '', 1, '2025-05-19 11:22:27', NULL);
INSERT INTO `repair_complaint` VALUES (11, 'repair', '12525', '网络维修', ' ', ' ', '', 1, '2025-05-19 11:28:50', NULL);
INSERT INTO `repair_complaint` VALUES (12, 'repair', '12525', '网络维修', ' ', ' ', '', 1, '2025-05-19 11:30:44', NULL);
INSERT INTO `repair_complaint` VALUES (13, 'repair', '1111', '设备维修', ' ', ' ', '', 1, '2025-05-19 11:31:29', NULL);
INSERT INTO `repair_complaint` VALUES (14, 'repair', 'sss', '设备维修', ' ', ' ', '', 1, '2025-05-21 16:30:54', NULL);
INSERT INTO `repair_complaint` VALUES (15, 'repair', '12舍525', '网络维修', ' ', ' ', '', 1, '2025-05-21 19:29:09', NULL);
INSERT INTO `repair_complaint` VALUES (16, 'complaint', '', NULL, ' ', '你是一个一个', '王万古', 1, '2025-05-21 19:58:29', NULL);
INSERT INTO `repair_complaint` VALUES (17, 'repair', '你是一个一个', '水电维修', ' ', ' ', '', 1, '2025-05-21 20:11:33', NULL);
INSERT INTO `repair_complaint` VALUES (18, 'repair', '和卢月整合', '设备维修', ' ', ' ', '', 1, '2025-05-21 20:50:05', NULL);
INSERT INTO `repair_complaint` VALUES (19, 'complaint', '', NULL, ' ', '不想写代码', '王万古', 1, '2025-05-21 21:02:27', NULL);
INSERT INTO `repair_complaint` VALUES (20, 'repair', 'yinbocode', '设备维修', ' ', ' ', '', 1, '2025-05-23 20:35:00', NULL);
INSERT INTO `repair_complaint` VALUES (21, 'repair', '银波codefix2.0', '水电维修', ' ', ' ', '', 1, '2025-05-23 23:42:44', NULL);
INSERT INTO `repair_complaint` VALUES (22, 'repair', 'assad', '网络维修', ' ', ' ', '', 1, '2025-05-24 00:33:20', NULL);
INSERT INTO `repair_complaint` VALUES (23, 'repair', '校本部12舍525', '水电维修', ' ', ' ', '', 1, '2025-05-24 00:37:19', NULL);
INSERT INTO `repair_complaint` VALUES (24, 'complaint', '', NULL, ' ', '熬夜写代码', '7', 1, '2025-05-24 10:03:29', NULL);
INSERT INTO `repair_complaint` VALUES (25, 'repair', '奥雷', '设备维修', ' ', ' ', '', 1, '2025-05-24 10:04:34', 1);
INSERT INTO `repair_complaint` VALUES (26, 'complaint', '', NULL, ' ', 'haodihen', '9', 1, '2025-05-24 10:04:43', 0);
INSERT INTO `repair_complaint` VALUES (27, 'repair', 'eds', '设备维修', ' ', ' ', '', 1, '2025-05-26 14:52:58', NULL);
INSERT INTO `repair_complaint` VALUES (28, 'complaint', '', NULL, ' ', '啊啊啊啊啊', '8', 1, '2025-05-26 15:21:52', NULL);
INSERT INTO `repair_complaint` VALUES (29, 'complaint', '', NULL, ' ', '整合修bug\noss都怪你', '7', 1, '2025-05-26 16:15:49', NULL);
INSERT INTO `repair_complaint` VALUES (30, 'complaint', '', NULL, ' ', '333333', '8', 1, '2025-05-30 22:36:26', NULL);
INSERT INTO `repair_complaint` VALUES (31, 'complaint', '天心', NULL, ' ', '什么公寓？就是茅舍', '杨公寓', 1, '2025-05-31 16:28:35', NULL);
INSERT INTO `repair_complaint` VALUES (32, 'complaint', NULL, NULL, ' ', '不租了', '穗露公寓', 1, '2025-05-31 16:50:26', NULL);
INSERT INTO `repair_complaint` VALUES (33, 'repair', '望城', '水电维修', ' ', ' ', '赵租房', 1, '2025-05-31 19:03:36', NULL);
INSERT INTO `repair_complaint` VALUES (34, 'repair', '雨花区井湾子融城花苑', '水电维修', ' ', ' ', '赵先生', 1, '2026-05-08 15:32:29', NULL);
INSERT INTO `repair_complaint` VALUES (35, 'complaint', '雨花区井湾子融城花苑', NULL, ' ', '不及时处理', '赵先生', 1, '2026-05-08 15:32:39', NULL);
INSERT INTO `repair_complaint` VALUES (36, 'repair', '雨花区井湾子融城花苑', '网络维修', ' ', ' ', '赵先生', 1, '2026-05-08 16:49:00', NULL);
INSERT INTO `repair_complaint` VALUES (37, 'repair', '芙蓉区树木岭锦源小区', '水电维修', ' ', ' ', '张先生', 1, '2026-05-09 15:50:18', NULL);
INSERT INTO `repair_complaint` VALUES (38, 'complaint', '芙蓉区树木岭锦源小区', NULL, ' ', 'ggg', '张先生', 1, '2026-05-09 15:50:24', NULL);
INSERT INTO `repair_complaint` VALUES (39, 'repair', '测试小区1栋101', '水管漏水', '厨房水龙头漏水严重', ' ', '', 1, '2026-05-11 15:42:16', NULL);
INSERT INTO `repair_complaint` VALUES (40, 'complaint', '测试小区2栋202', '服务态度', ' ', '房东态度恶劣', '测试房东', 1, '2026-05-11 15:42:16', NULL);
INSERT INTO `repair_complaint` VALUES (41, 'repair', '测试小区1栋101', '水管漏水', '厨房水龙头漏水严重', ' ', '', 1, '2026-05-11 15:43:51', NULL);
INSERT INTO `repair_complaint` VALUES (42, 'complaint', '测试小区2栋202', '服务态度', ' ', '房东态度恶劣', '测试房东', 1, '2026-05-11 15:43:51', NULL);
INSERT INTO `repair_complaint` VALUES (43, 'repair', '测试小区1栋101', '水管漏水', '厨房水龙头漏水严重', ' ', '', 1, '2026-05-11 15:48:33', NULL);
INSERT INTO `repair_complaint` VALUES (44, 'complaint', '测试小区2栋202', '服务态度', ' ', '房东态度恶劣', '测试房东', 1, '2026-05-11 15:48:33', NULL);
INSERT INTO `repair_complaint` VALUES (45, 'repair', '测试小区1栋101', '水管漏水', '厨房水龙头漏水严重', ' ', '', 1, '2026-05-11 15:50:07', NULL);
INSERT INTO `repair_complaint` VALUES (46, 'complaint', '测试小区2栋202', '服务态度', ' ', '房东态度恶劣', '测试房东', 1, '2026-05-11 15:50:07', NULL);
INSERT INTO `repair_complaint` VALUES (47, 'repair', '测试小区1栋101', '水管漏水', '厨房水龙头漏水严重', ' ', '', 1, '2026-05-11 15:51:43', NULL);
INSERT INTO `repair_complaint` VALUES (48, 'complaint', '测试小区2栋202', '服务态度', ' ', '房东态度恶劣', '测试房东', 1, '2026-05-11 15:51:43', NULL);
INSERT INTO `repair_complaint` VALUES (49, 'repair', '测试小区1栋101室', '水管漏水', '厨房水龙头漏水严重，需要紧急维修', ' ', '', 1, '2026-05-11 16:12:52', NULL);
INSERT INTO `repair_complaint` VALUES (50, 'repair', '测试小区2栋202', '电路故障', ' ', ' ', '', 1, '2026-05-11 16:12:52', NULL);
INSERT INTO `repair_complaint` VALUES (51, 'complaint', '测试小区3栋303', '服务态度问题', ' ', '房东多次无故拖延维修，态度恶劣', '不良房东', 1, '2026-05-11 16:12:52', NULL);
INSERT INTO `repair_complaint` VALUES (52, 'complaint', '测试小区4栋404', '房屋设施损坏', ' ', ' ', '', 1, '2026-05-11 16:12:52', NULL);
INSERT INTO `repair_complaint` VALUES (53, 'repair', 'test address', 'test type', ' ', ' ', '', 1, '2026-05-11 16:12:52', NULL);
INSERT INTO `repair_complaint` VALUES (54, 'repair', 'test', 'test', ' ', ' ', '', 0, '2026-05-11 16:12:52', NULL);
INSERT INTO `repair_complaint` VALUES (55, 'repair', '测试小区1栋101室', '水管漏水', '厨房水龙头漏水严重，需要紧急维修', ' ', '', 1, '2026-05-11 16:15:19', NULL);
INSERT INTO `repair_complaint` VALUES (56, 'repair', '测试小区2栋202', '电路故障', ' ', ' ', '', 1, '2026-05-11 16:15:19', NULL);
INSERT INTO `repair_complaint` VALUES (57, 'complaint', '测试小区3栋303', '服务态度问题', ' ', '房东多次无故拖延维修，态度恶劣', '不良房东', 1, '2026-05-11 16:15:19', NULL);
INSERT INTO `repair_complaint` VALUES (58, 'complaint', '测试小区4栋404', '房屋设施损坏', ' ', ' ', '', 1, '2026-05-11 16:15:19', NULL);
INSERT INTO `repair_complaint` VALUES (59, 'repair', 'test address', 'test type', ' ', ' ', '', 1, '2026-05-11 16:15:19', NULL);
INSERT INTO `repair_complaint` VALUES (60, 'repair', 'test', 'test', ' ', ' ', '', 0, '2026-05-11 16:15:19', NULL);
INSERT INTO `repair_complaint` VALUES (61, 'repair', '测试小区1栋101室', '水管漏水', '厨房水龙头漏水严重，需要紧急维修', ' ', '', 1, '2026-05-11 16:16:53', NULL);
INSERT INTO `repair_complaint` VALUES (62, 'repair', '测试小区2栋202', '电路故障', ' ', ' ', '', 1, '2026-05-11 16:16:53', NULL);
INSERT INTO `repair_complaint` VALUES (63, 'complaint', '测试小区3栋303', '服务态度问题', ' ', '房东多次无故拖延维修，态度恶劣', '不良房东', 1, '2026-05-11 16:16:53', NULL);
INSERT INTO `repair_complaint` VALUES (64, 'complaint', '测试小区4栋404', '房屋设施损坏', ' ', ' ', '', 1, '2026-05-11 16:16:53', NULL);
INSERT INTO `repair_complaint` VALUES (65, 'repair', 'test address', 'test type', ' ', ' ', '', 1, '2026-05-11 16:16:53', NULL);
INSERT INTO `repair_complaint` VALUES (66, 'repair', 'test', 'test', ' ', ' ', '', 0, '2026-05-11 16:16:53', NULL);
INSERT INTO `repair_complaint` VALUES (67, 'repair', '测试小区1栋101室', '水管漏水', '厨房水龙头漏水严重，需要紧急维修', ' ', '', 1, '2026-05-11 16:19:01', NULL);
INSERT INTO `repair_complaint` VALUES (68, 'repair', '测试小区2栋202', '电路故障', ' ', ' ', '', 1, '2026-05-11 16:19:01', NULL);
INSERT INTO `repair_complaint` VALUES (69, 'complaint', '测试小区3栋303', '服务态度问题', ' ', '房东多次无故拖延维修，态度恶劣', '不良房东', 1, '2026-05-11 16:19:01', NULL);
INSERT INTO `repair_complaint` VALUES (70, 'complaint', '测试小区4栋404', '房屋设施损坏', ' ', ' ', '', 1, '2026-05-11 16:19:01', NULL);
INSERT INTO `repair_complaint` VALUES (71, 'repair', 'test address', 'test type', ' ', ' ', '', 1, '2026-05-11 16:19:01', NULL);
INSERT INTO `repair_complaint` VALUES (72, 'repair', 'test', 'test', ' ', ' ', '', 0, '2026-05-11 16:19:01', NULL);
INSERT INTO `repair_complaint` VALUES (73, 'repair', '测试小区1栋101室', '水管漏水', '厨房水龙头漏水严重，需要紧急维修', ' ', '', 1, '2026-05-11 16:23:16', NULL);
INSERT INTO `repair_complaint` VALUES (74, 'repair', '测试小区2栋202', '电路故障', ' ', ' ', '', 1, '2026-05-11 16:23:16', NULL);
INSERT INTO `repair_complaint` VALUES (75, 'complaint', '测试小区3栋303', '服务态度问题', ' ', '房东多次无故拖延维修，态度恶劣', '不良房东', 1, '2026-05-11 16:23:16', NULL);
INSERT INTO `repair_complaint` VALUES (76, 'complaint', '测试小区4栋404', '房屋设施损坏', ' ', ' ', '', 1, '2026-05-11 16:23:16', NULL);
INSERT INTO `repair_complaint` VALUES (77, 'repair', 'test address', 'test type', ' ', ' ', '', 1, '2026-05-11 16:23:16', NULL);
INSERT INTO `repair_complaint` VALUES (78, 'repair', 'test', 'test', ' ', ' ', '', 0, '2026-05-11 16:23:16', NULL);
INSERT INTO `repair_complaint` VALUES (79, 'repair', '长沙县区泉塘楚天世纪城', '网络维修', ' ', ' ', '吴先生', 1, '2026-05-11 17:12:44', NULL);

-- ----------------------------
-- Table structure for user_info
-- ----------------------------
DROP TABLE IF EXISTS `user_info`;
CREATE TABLE `user_info`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `phone` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `addr` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `seen_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `collect_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `identityCard` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `userType` int NULL DEFAULT NULL,
  `avatarUrl` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 26 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of user_info
-- ----------------------------
INSERT INTO `user_info` VALUES (1, '更新测试名称', '$2b$12$jZWPYtA7PCAIkvQ1ANAxvuw9R7fjVFEyFwjEEjZiQrRgw9.erbfhi', '2779902@qq.com', '13630278915', '北京市朝阳区测试路100号', '0', '0', '325896522310202589', 2, 'http://localhost:5000/user/images/1_20250620070014.jpg');
INSERT INTO `user_info` VALUES (3, 'Ylfmoonn', '$2b$12$yFwVyAF0jXPaB4jEx3.MZeOG8FzRe2Mnvg5cMQyiJpWg0hvpLg/qK', 'lapu2023@outlook.com', '19511053623', '岳麓区', '1', '2', '41132511451411', 2, 'http://localhost:5000/user/images/3_20250620081857.jpg');
INSERT INTO `user_info` VALUES (4, 'Lappand', '$2b$12$bA1jsIhsQi/qTGAilYyLF.EV0v3EHkl5qcpBGxBmWJRH/LPHsUchq', '1769850997@qq.com', '19511053624', '校本部1111', NULL, NULL, NULL, 0, 'https://flaskhousesystem.oss-cn-hangzhou.aliyuncs.com/house_images/3/82d3513094144b92abfe5a20419d82e9.png');
INSERT INTO `user_info` VALUES (5, NULL, '$2b$12$BKQ4MnXq8qnvz4SownzK3uoBCdmRktRdr2BX4FlzjT/7xBjGXzyqS', NULL, '15274896231', NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `user_info` VALUES (6, NULL, '$2b$12$ChX6QeErNGea10kbGHpLSeOlJVX4iW2t/OxGthi3.F38IhQzBitl2', NULL, '195110536232', NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `user_info` VALUES (8, '胡琪', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2, NULL);
INSERT INTO `user_info` VALUES (9, '梅姨', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 2, NULL);
INSERT INTO `user_info` VALUES (10, NULL, '$2b$12$N/yOiQTDtKMI.gzO00VoBeZjHUwI.5hZ/KzaEoLJPGEsl3CM4KLCS', NULL, '15083377951', NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `user_info` VALUES (11, 'luyue', '$2b$12$r6AxUuDxoFHNjktrDuuCG.MVjSqcVMwtWzzkEZVDXQitpoFoqxuS.', '114514@qq.com', '16608188855', '下北泽', NULL, NULL, '111111111111111111', 1, NULL);
INSERT INTO `user_info` VALUES (12, 'TEST', '$2b$12$NUI4p9sW.ife70zTv9XXnuCwGln5c2Wddfy17TKn8/1IfaA8YPiya', '2222344555322@qq.com', '09876543210', 'NONONO', NULL, NULL, '221020366502040256', NULL, NULL);
INSERT INTO `user_info` VALUES (13, 'Andy_LIN', '$2b$12$Dv8BbVPY5DqNsFA3ADv0U.EmQk5rv6Pj4GTOhMNWcnUQvodJfBx/e', '5230015682@qq.com', '18992677643', 'CSU', NULL, NULL, '522020100250203026', 2, 'http://localhost:5000/user/images/13_20250612120753.jpg');
INSERT INTO `user_info` VALUES (15, NULL, '$2b$12$5g6HZGYJnHVGULaOLMTshevMck8zjXJDdboruvBqIoF8ePpNvJYQq', '84532@qq.com', '7539514682', NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `user_info` VALUES (16, 'Andy_gitub', '$2b$12$54ICuD5xVGyZJib0qeCyfe6zH6eoc2DW430OpVp/wounLdWg8qvy2', '2298786941@qq.com', '0916-2566302', 'America', NULL, NULL, '562023000582012036', 1, 'http://localhost:5000/user/images/16_20250612121326.jpg');
INSERT INTO `user_info` VALUES (18, 'manba', '$2b$12$kAaYpq2M2k6.dgUbqxtkWu4Zr9KhFZLg9xlyVEoO.0fmNiRefx.cK', '2779902707@qq.com', '16608188853', '12525', NULL, NULL, '111111111111111111', 2, 'http://localhost:5000/user/images/18_20250612124635.jpg');
INSERT INTO `user_info` VALUES (19, NULL, '$2b$12$1X3F0LA1A1ng..IxwVCd.Oy2kK9RsqZKMf8LTnwnuT5lEytQnXVB6', 'autotest_user@test.com', '19900000001', NULL, NULL, NULL, NULL, 2, NULL);
INSERT INTO `user_info` VALUES (20, NULL, '$2b$12$9yNUUIaHPdpohN/JFpUY3etGRMTr1Eb9BGutpxwaTVsQYA./hRome', 'user_by_name@test.com', '19911111111', NULL, NULL, NULL, NULL, 1, NULL);
INSERT INTO `user_info` VALUES (21, NULL, '$2b$12$y3evcpqCzBsarRipRytdZe91DhSTWZbNxcLrVurMf85pEPc1MDma.', 'test_5466a2e0@autotest.com', '19923489193', NULL, NULL, NULL, NULL, 1, NULL);
INSERT INTO `user_info` VALUES (22, NULL, '$2b$12$gkxm4ltJl6ymtlBn8J7TEunsA1RX4bM4oohoiVlSQwT36WV6UyYsS', 'test_69a8fe1c@autotest.com', '19933784518', NULL, NULL, NULL, NULL, 1, NULL);
INSERT INTO `user_info` VALUES (23, NULL, '$2b$12$Pl9JhD1ItiE1jR7GtXacMO/5dK7aQdtDk4QQDthDlpFiyXboCOy6y', 'test_aa3538cb@autotest.com', '19992072164', NULL, NULL, NULL, NULL, 1, NULL);
INSERT INTO `user_info` VALUES (24, NULL, '$2b$12$Tg2ooDCuJZRgQkP1PamSgu6OZGCIPYlZ8dtmlVpge2XzuGVox2aFu', 'test_3d4e351b@autotest.com', '19938904711', NULL, NULL, NULL, NULL, 1, NULL);
INSERT INTO `user_info` VALUES (25, NULL, '$2b$12$Np1r1lEt.ujmx.i56SgBIOux/yh/K9BaDs8YC/RJlkUJhed5Emple', 'test_cff047ca@autotest.com', '19923803170', NULL, NULL, NULL, NULL, 1, NULL);

-- ----------------------------
-- FastAPI schema sync (Alembic head: 006_ai_agent_runs)
-- Keep this section after all legacy INSERT statements so their positional
-- value counts remain valid. New identifiers are nullable because historical
-- names and phone numbers are not globally unique.
-- ----------------------------
ALTER TABLE `contract`
  ADD COLUMN `payment_status` varchar(20) NULL DEFAULT 'pending' COMMENT 'Payment state: pending/paid/cancelled/expired',
  ADD COLUMN `payment_trade_no` varchar(64) NULL DEFAULT NULL COMMENT 'Alipay out_trade_no for idempotency',
  ADD COLUMN `paid_at` datetime NULL DEFAULT NULL COMMENT 'Timestamp when payment was confirmed',
  ADD COLUMN `expires_at` datetime NULL DEFAULT NULL;

CREATE UNIQUE INDEX `ix_contract_payment_trade_no`
  ON `contract` (`payment_trade_no` ASC);
CREATE INDEX `ix_contract_expires_at`
  ON `contract` (`expires_at` ASC);

ALTER TABLE `house_info`
  ADD COLUMN `landlord_id` int NULL DEFAULT NULL;
CREATE INDEX `ix_house_info_landlord_id`
  ON `house_info` (`landlord_id` ASC);

ALTER TABLE `rental`
  ADD COLUMN `contract_id` int NULL DEFAULT NULL,
  ADD COLUMN `tenant_id` int NULL DEFAULT NULL,
  ADD COLUMN `landlord_id` int NULL DEFAULT NULL;
CREATE UNIQUE INDEX `uq_rental_contract_id`
  ON `rental` (`contract_id` ASC);
CREATE INDEX `ix_rental_tenant_id`
  ON `rental` (`tenant_id` ASC);
CREATE INDEX `ix_rental_landlord_id`
  ON `rental` (`landlord_id` ASC);

-- Conservative legacy ownership backfill: only unique identities are linked.
UPDATE `house_info` AS h
JOIN (
  SELECT `phone`, MIN(`id`) AS `user_id`
  FROM `user_info`
  WHERE `phone` IS NOT NULL AND `phone` <> ''
  GROUP BY `phone`
  HAVING COUNT(*) = 1
) AS u ON u.`phone` = h.`phone_num`
SET h.`landlord_id` = u.`user_id`
WHERE h.`landlord_id` IS NULL;

UPDATE `rental` AS r
JOIN (
  SELECT `name`, MIN(`id`) AS `user_id`
  FROM `user_info`
  WHERE `name` IS NOT NULL AND `name` <> ''
  GROUP BY `name`
  HAVING COUNT(*) = 1
) AS u ON u.`name` = r.`tenant_username`
SET r.`tenant_id` = u.`user_id`
WHERE r.`tenant_id` IS NULL;

UPDATE `rental` AS r
JOIN `house_info` AS h ON h.`id` = r.`house_id`
SET r.`landlord_id` = h.`landlord_id`
WHERE r.`landlord_id` IS NULL AND h.`landlord_id` IS NOT NULL;

-- Historical contract data is ambiguous, so rental.contract_id is not guessed.
ALTER TABLE `channel`
  ADD COLUMN `tenant_id` int NULL,
  ADD COLUMN `landlord_id` int NULL,
  ADD INDEX `ix_channel_tenant_id` (`tenant_id`),
  ADD INDEX `ix_channel_landlord_id` (`landlord_id`);

ALTER TABLE `message`
  ADD COLUMN `sender_id` int NULL,
  ADD COLUMN `receiver_id` int NULL,
  ADD INDEX `ix_message_sender_id` (`sender_id`),
  ADD INDEX `ix_message_receiver_id` (`receiver_id`);

UPDATE `channel` AS target
JOIN (SELECT `name`, MIN(`id`) AS user_id FROM `user_info` WHERE `name` IS NOT NULL AND `name` <> '' GROUP BY `name` HAVING COUNT(*) = 1) AS users
  ON users.`name` = target.`tenant_username`
SET target.`tenant_id` = users.user_id;
UPDATE `channel` AS target
JOIN (SELECT `name`, MIN(`id`) AS user_id FROM `user_info` WHERE `name` IS NOT NULL AND `name` <> '' GROUP BY `name` HAVING COUNT(*) = 1) AS users
  ON users.`name` = target.`landlord_username`
SET target.`landlord_id` = users.user_id;
UPDATE `message` AS target
JOIN (SELECT `name`, MIN(`id`) AS user_id FROM `user_info` WHERE `name` IS NOT NULL AND `name` <> '' GROUP BY `name` HAVING COUNT(*) = 1) AS users
  ON users.`name` = target.`sender_username`
SET target.`sender_id` = users.user_id;
UPDATE `message` AS target
JOIN (SELECT `name`, MIN(`id`) AS user_id FROM `user_info` WHERE `name` IS NOT NULL AND `name` <> '' GROUP BY `name` HAVING COUNT(*) = 1) AS users
  ON users.`name` = target.`receiver_username`
SET target.`receiver_id` = users.user_id;

DROP TABLE IF EXISTS `ai_agent_run`;
CREATE TABLE `ai_agent_run` (
  `request_id` varchar(36) NOT NULL,
  `user_id` int NOT NULL,
  `session_id` int NOT NULL,
  `user_message_id` int NOT NULL,
  `assistant_message_id` int NULL,
  `status` varchar(20) NOT NULL DEFAULT 'running',
  `cancel_requested` tinyint(1) NOT NULL DEFAULT 0,
  `error_code` varchar(50) NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`request_id`),
  UNIQUE KEY `uq_ai_agent_run_user_message_id` (`user_message_id`),
  UNIQUE KEY `uq_ai_agent_run_assistant_message_id` (`assistant_message_id`),
  KEY `ix_ai_agent_run_user_id` (`user_id`),
  KEY `ix_ai_agent_run_session_id` (`session_id`),
  KEY `ix_ai_agent_run_status` (`status`),
  CONSTRAINT `fk_ai_agent_run_user` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ai_agent_run_session` FOREIGN KEY (`session_id`) REFERENCES `chat_session` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ai_agent_run_user_message` FOREIGN KEY (`user_message_id`) REFERENCES `chat_message` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ai_agent_run_assistant_message` FOREIGN KEY (`assistant_message_id`) REFERENCES `chat_message` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
INSERT INTO `alembic_version` (`version_num`)
VALUES ('006_ai_agent_runs');

SET FOREIGN_KEY_CHECKS = 1;
