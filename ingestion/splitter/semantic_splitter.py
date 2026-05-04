import json
from pathlib import Path

from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document

from ingestion.config.embedding import OpenAIEmbeddingLangchain

# Data under ingestion/ (splitter -> ingestion -> data)
_INGESTION_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _INGESTION_ROOT / "data"
_DATASET = "exp-g11-bio"
_CHAPTER = "chapter_3"
INPUT_JSON = DATA_DIR / "load" / _DATASET / _CHAPTER / "doc-loader-main-2.json"
OUTPUT_JSON = DATA_DIR / "prepare" / _DATASET / _CHAPTER / "split-docs-main-75.json"


def main() -> None:
    print("Loading normalized docs...")
    with INPUT_JSON.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in payload]
    print(f"Loaded {len(docs)} document(s).")

    embeddings = OpenAIEmbeddingLangchain()

    print("Splitting docs semantically...")
    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=75,
    )

    split_docs = splitter.split_documents(docs)
    print(f"Split into {len(split_docs)} chunk(s).")

    print("Saving split docs...")
    output = [{"page_content": d.page_content, "metadata": d.metadata} for d in split_docs]
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
