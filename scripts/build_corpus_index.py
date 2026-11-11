"""Build the BM25 index of the corpus one parquet file at a time, to keep memory low."""
import argparse
import json
import resource
from pathlib import Path

import bm25s
import pyarrow.parquet as pq
from bm25s.tokenization import Tokenizer


def peak_gb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2


def main(corpus_dir: Path, index_path: Path, docids_path: Path, max_docs: int | None) -> None:
    tokenizer = Tokenizer(stopwords="en")
    docids, token_ids = [], []
    for path in sorted(corpus_dir.glob("*.parquet")):
        # Text is dropped after each file; only docid and token ids are kept.
        table = pq.read_table(path, columns=["docid", "text"])
        if max_docs is not None:
            table = table.slice(0, max_docs - len(docids))
        docids.extend(table.column("docid").to_pylist())
        token_ids.extend(tokenizer.tokenize(table.column("text").to_pylist(), return_as="ids", show_progress=False))
        del table
        print(f"{path.name}: {len(docids)} documents, peak {peak_gb():.2f} GB", flush=True)
        if max_docs is not None and len(docids) >= max_docs:
            break

    retriever = bm25s.BM25()
    retriever.index((token_ids, tokenizer.get_vocab_dict()), show_progress=False)
    print(f"Indexed {len(docids)} documents, peak {peak_gb():.2f} GB", flush=True)

    # Written last, so that the docid file marks a finished index.
    retriever.save(index_path)
    docids_path.write_text(json.dumps(docids))
    print(f"Saved {index_path}, peak {peak_gb():.2f} GB", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_dir", type=Path)
    parser.add_argument("index_path", type=Path)
    parser.add_argument("docids_path", type=Path)
    parser.add_argument("--max-docs", type=int, help="index only this many documents, for testing")
    args = parser.parse_args()
    main(args.corpus_dir, args.index_path, args.docids_path, args.max_docs)
