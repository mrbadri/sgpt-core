import argparse
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path

from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document

from ingestion.config.embedding import OpenAIEmbeddingLangchain

# Data under ingestion/ (splitter -> ingestion -> data)
_INGESTION_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _INGESTION_ROOT / "data"
_DATASET = "exp-g11-bio"
INPUT_JSON = DATA_DIR / "load" / _DATASET / "exp-g11-bio-1404.json"
OUTPUT_JSON = DATA_DIR / "prepare" / _DATASET / "exp-g11-bio-1404.json"

SOURCE_INDEX_META_KEY = "semantic_split_source_index"

logger = logging.getLogger(__name__)


class _C:
    """ANSI; disabled with NO_COLOR or non-TTY stderr."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GRAY = "\033[38;5;246m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[97m"


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stderr.isatty()


class SemanticSplitColorFormatter(logging.Formatter):
    """Timestamp + level badge + message accents for semantic split CLI."""

    datefmt = "%H:%M:%S"

    _LEVEL_COL = {
        logging.DEBUG: _C.CYAN,
        logging.INFO: _C.GREEN,
        logging.WARNING: _C.YELLOW,
        logging.ERROR: _C.RED,
        logging.CRITICAL: _C.RED + _C.BOLD,
    }

    _PREFIX_ACCENT = (
        ("Loading normalized docs from ", _C.BLUE + _C.BOLD),
        ("Loaded ", _C.GREEN + _C.BOLD),
        ("Resuming from ", _C.YELLOW + _C.BOLD),
        ("Splitting source document ", _C.CYAN + _C.BOLD),
        ("chunk ", _C.CYAN + _C.BOLD),
        ("Checkpoint: ", _C.MAGENTA + _C.BOLD),
        ("Done. Saved ", _C.GREEN + _C.BOLD),
        ("Could not read existing output ", _C.YELLOW),
        ("Output ", _C.RED + _C.BOLD),
    )

    _KV_SPLIT = re.compile(
        r"(global_idx|src_idx|part|chars|chunk_total|source_docs|source|next_src_idx|chunks_saved|last_src_idx)=(\S+)"
    )

    def __init__(self) -> None:
        super().__init__(fmt="%(message)s", datefmt=self.datefmt)
        self._color = _use_color()

    def _badge(self, record: logging.LogRecord) -> str:
        if not self._color:
            return f"{record.levelname:<9} |"
        col = self._LEVEL_COL.get(record.levelno, _C.WHITE)
        bar = _C.GRAY + _C.DIM + " |" + _C.RESET
        return f"{col}{_C.BOLD}{record.levelname:<9}{_C.RESET}{bar}"

    def _shade_kv_plain(self, msg: str) -> str:
        if not self._color:
            return msg
        vk_for = {
            "global_idx": _C.YELLOW,
            "src_idx": _C.MAGENTA,
            "part": _C.BLUE,
            "chars": _C.GRAY,
            "chunk_total": _C.GREEN,
            "source_docs": _C.BLUE,
            "source": _C.BLUE,
            "next_src_idx": _C.YELLOW,
            "chunks_saved": _C.GREEN,
            "last_src_idx": _C.MAGENTA,
        }
        fragments: list[str] = []
        prev = 0
        for m in self._KV_SPLIT.finditer(msg):
            if prev < m.start():
                fragments.append(_C.WHITE + msg[prev:m.start()] + _C.RESET)
            key, val = m.group(1), m.group(2)
            vk = vk_for.get(key, _C.GRAY)
            fragments.append(f"{_C.DIM}{key}={_C.RESET}{_C.BOLD}{vk}{val}{_C.RESET}")
            prev = m.end()
        fragments.append(_C.WHITE + msg[prev:] + _C.RESET)
        return "".join(fragments)

    def _shade_message(self, msg: str) -> str:
        if not self._color:
            return msg

        split_sep = " \u2502 "
        if split_sep in msg:
            left, right = msg.split(split_sep, 1)
            shaded_left = self._shade_kv_plain(left)
            return shaded_left + _C.GRAY + split_sep + _C.RESET + _C.DIM + right + _C.RESET

        for pref, cc in self._PREFIX_ACCENT:
            if msg.startswith(pref):
                tail = msg[len(pref) :]
                return cc + pref + _C.RESET + self._shade_kv_plain(tail)
        return self._shade_kv_plain(msg)

    def format(self, record: logging.LogRecord) -> str:
        ts_prefix = (
            f"{_C.GRAY}{self.formatTime(record, self.datefmt)}{_C.RESET} "
            if self._color
            else f"{self.formatTime(record, self.datefmt)} "
        )
        shaded = self._shade_message(record.getMessage())
        line = f"{ts_prefix}{self._badge(record)} {shaded}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        elif record.exc_text:
            line += "\n" + record.exc_text
        return line


def _configure_semantic_split_logging(*, level: int = logging.INFO) -> None:
    log = logging.getLogger(__name__)
    log.handlers.clear()
    log.setLevel(level)
    log.propagate = False
    h = logging.StreamHandler(sys.stderr)
    h.setLevel(level)
    h.setFormatter(SemanticSplitColorFormatter())
    log.addHandler(h)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        suffix=".json.tmp",
        prefix=path.name + ".",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _next_source_index_from_output(path: Path) -> tuple[int, list[dict]]:
    if not path.is_file():
        return 0, []
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read existing output %s (%s); starting fresh.", path, e)
        return 0, []

    if not isinstance(payload, list):
        return 0, []

    indices = [
        item["metadata"].get(SOURCE_INDEX_META_KEY)
        for item in payload
        if isinstance(item, dict)
        and isinstance(item.get("metadata"), dict)
        and SOURCE_INDEX_META_KEY in item["metadata"]
    ]
    if payload and not indices:
        logger.error(
            "Output %s exists but has no %r in metadata — cannot resume safely "
            "(would overwrite). Back it up, then use --fresh.",
            path,
            SOURCE_INDEX_META_KEY,
        )
        sys.exit(1)
    if not indices:
        return 0, []

    next_i = max(indices) + 1
    return next_i, payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic split with per-chunk logs and resume.")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing output and split all source documents from the beginning.",
    )
    args = parser.parse_args()

    _configure_semantic_split_logging(level=logging.INFO)

    logger.info("Loading normalized docs from %s", INPUT_JSON)
    with INPUT_JSON.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in payload]
    logger.info("Loaded source_docs=%s.", len(docs))

    if args.fresh:
        accumulated: list[dict] = []
        start_at = 0
    else:
        start_at, accumulated = _next_source_index_from_output(OUTPUT_JSON)
        if start_at > 0:
            logger.info(
                "Resuming from next_src_idx=%s chunks_saved=%s.",
                start_at,
                len(accumulated),
            )

    embeddings = OpenAIEmbeddingLangchain()

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=75,
    )

    global_chunk_offset = len(accumulated)

    for src_idx in range(start_at, len(docs)):
        doc = docs[src_idx]
        logger.info(
            "Splitting source document source=%s/%s chars=%s.",
            src_idx + 1,
            len(docs),
            len(doc.page_content),
        )

        split_docs = splitter.split_documents([doc])

        for j, chunk in enumerate(split_docs):
            meta = dict(chunk.metadata)
            meta[SOURCE_INDEX_META_KEY] = src_idx
            row = {"page_content": chunk.page_content, "metadata": meta}
            accumulated.append(row)

            preview = chunk.page_content.replace("\n", " ").strip()[:120]
            if len(chunk.page_content) > 120:
                preview = preview + "..."
            sep = " \u2502 "
            logger.info(
                "chunk global_idx=%s src_idx=%s part=%s chars=%s%s%s",
                global_chunk_offset + j,
                src_idx,
                f"{j + 1}/{len(split_docs)}",
                len(chunk.page_content),
                sep,
                preview,
            )

        global_chunk_offset = len(accumulated)

        _atomic_write_json(OUTPUT_JSON, accumulated)
        logger.info(
            "Checkpoint: chunk_total=%s last_src_idx=%s.",
            len(accumulated),
            src_idx,
        )

    logger.info(
        "Done. Saved chunk_total=%s chunks to %s.",
        len(accumulated),
        OUTPUT_JSON,
    )


if __name__ == "__main__":
    main()
