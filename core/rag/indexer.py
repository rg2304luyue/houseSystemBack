"""CLI for safe knowledge-index synchronization."""
import argparse
import json
from core.rag.vector_store_v2 import VectorStoreServiceV2


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize the rental RAG knowledge index")
    parser.add_argument("--rebuild", action="store_true", help="Reset and rebuild the collection")
    args = parser.parse_args()
    print(json.dumps(VectorStoreServiceV2().sync_documents(rebuild=args.rebuild).to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
