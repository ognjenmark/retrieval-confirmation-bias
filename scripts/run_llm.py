"""Run a local GGUF model over a JSONL file of prompts; resumes where a previous run stopped."""
import argparse
import json
import re
import time
from pathlib import Path

from llama_cpp import Llama

THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def main(model_path: Path, prompts_path: Path, outputs_path: Path, max_tokens: int, n_ctx: int, threads: int) -> None:
    prompts = [json.loads(line) for line in prompts_path.read_text().splitlines()]
    done = set()
    if outputs_path.exists():
        done = {json.loads(line)["id"] for line in outputs_path.read_text().splitlines()}
    todo = [p for p in prompts if p["id"] not in done]
    print(f"{len(prompts)} prompts, {len(done)} already done, {len(todo)} to run", flush=True)
    if not todo:
        return

    llm = Llama(str(model_path), n_ctx=n_ctx, n_threads=threads, seed=0, verbose=False)
    start = time.time()
    with outputs_path.open("a", encoding="utf-8") as f:
        for i, prompt in enumerate(todo, start=1):
            response = llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt["prompt"]}],
                temperature=0.0, max_tokens=max_tokens, seed=0,
            )
            text = THINK.sub("", response["choices"][0]["message"]["content"]).strip()
            record = {"id": prompt["id"], "output": text, "prompt_tokens": response["usage"]["prompt_tokens"]}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            if i % 10 == 0 or i == len(todo):
                elapsed = time.time() - start
                print(f"{i}/{len(todo)} done, {elapsed / i:.1f} s per prompt", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("prompts_path", type=Path)
    parser.add_argument("outputs_path", type=Path)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()
    main(args.model_path, args.prompts_path, args.outputs_path, args.max_tokens, args.n_ctx, args.threads)
