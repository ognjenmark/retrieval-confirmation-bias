# Retrieval Confirmation Bias

Can search reject a wrong answer as reliably as it confirms a correct one?

Search agents often guess an answer first and then search to verify it, so the verification query contains the
guess ("Christopher Nolan director Arrival 2016"). Such a query may retrieve documents that merely *mention* the
guess instead of evidence that supports or refutes it. If so, search adds confidence without adding information,
and standard ranking metrics do not show it. This repository is an empirical study of that effect.

**Status: pilot, development questions only.** The pipeline runs on 100 development questions. The held-out test
questions (730) have not been run, manual labels are not entered yet, and only a lexical retriever (BM25) has
been tested. Results below are exploratory and may change on the test set.

## Hypotheses

- **H1, retrieval echo:** adding a wrong candidate answer to a query lowers recall and rank of documents that
  contain the correct answer, compared with a neutral query.
- **H2, asymmetry:** a correct candidate helps retrieval of supporting evidence more than a wrong candidate
  preserves retrieval of refuting evidence.
- **H3, retriever dependence:** the effect differs between lexical (BM25) and dense retrievers.
- **H4, reader:** a model that reads the results of a query containing a wrong candidate accepts that candidate
  more often than after reading the results of a neutral query.

All outcomes are reported, including null results.

## Setup

- **Data:** [BrowseComp-Plus](https://arxiv.org/abs/2508.06600) (Chen et al., MIT license): 830 questions with
  short unique answers, a fixed corpus of 100,195 web documents, and human-labeled gold documents per question.
- **Split:** 100 development / 730 test questions, fixed with seed 0 before any result was computed
  (`results/split.json`). All design choices are made on development questions only.
- **Queries** (per question):
  - `q0`: the full question;
  - `q_keywords`: the 20 question terms rarest in the corpus, the neutral baseline for all candidate queries;
  - `q_true`: `q_keywords` + the correct answer;
  - `q_wrong`: `q_keywords` + a plausible wrong answer, the first closed-book guess of a local LLM that is
    verified not to match the correct answer or appear in a gold document;
  - `q_random`: `q_keywords` + the answer of another question of the same type (control).
- **Retrieval:** BM25 (`bm25s`) over each question's candidate pool and over the full corpus. Metrics: recall@k of
  gold documents, rank of the first gold document, and number of top-k documents that mention the candidate.
- **Reader:** Qwen3-4B (Q4_K_M GGUF, `llama-cpp-python`, CPU, temperature 0) reads the top 5 documents of a query
  (200-word windows) and judges a proposed answer as SUPPORTED, REFUTED or UNCLEAR.
- **Uncertainty:** paired bootstrap 95% intervals over questions (2,000 resamples), not corrected for multiple
  comparisons.

## Pilot results (development questions)

**Retrieval (H1, H2).** A wrong candidate barely changes gold recall, while the correct answer raises it strongly.
H1 is not supported on this sample: the one interval that excludes zero (corpus recall@10) is a small drop.
Documents that mention the wrong candidate do rise in the top 10.

| Space | Metric | Gain from correct answer (95% CI) | Change from wrong candidate (95% CI) |
|---|---|---|---|
| pool | recall@5 | +0.385 (0.305 to 0.468) | +0.007 (-0.020 to 0.040) |
| pool | recall@10 | +0.428 (0.351 to 0.504) | +0.001 (-0.024 to 0.029) |
| pool | recall@20 | +0.452 (0.372 to 0.535) | -0.002 (-0.021 to 0.017) |
| corpus | recall@5 | +0.287 (0.218 to 0.363) | -0.008 (-0.021 to 0.000) |
| corpus | recall@10 | +0.305 (0.229 to 0.385) | -0.015 (-0.030 to -0.003) |
| corpus | recall@20 | +0.330 (0.252 to 0.413) | -0.008 (-0.017 to 0.000) |
| corpus | recall@100 | +0.451 (0.370 to 0.535) | +0.004 (-0.008 to 0.019) |
| corpus | recall@1000 | +0.470 (0.390 to 0.548) | +0.009 (-0.023 to 0.049) |

Source: `results/asymmetry_true_wrong_dev.csv`; changes are relative to `q_keywords`.

**Reader (H4).** The reader calls the wrong candidate SUPPORTED more often after reading `q_wrong` results than
after reading `q_keywords` results. A snippet control (`wrong_wrong_kwsnip`: `q_wrong` documents, windows chosen
by `q_keywords` terms) splits this difference into two parts of about equal size, one from the retrieved documents
and one from windows chosen by a query that contains the candidate; both parts are close to zero, so the split
is suggestive only. The snippet control was added after the first H4 result was seen.

| Comparison | Verdict | Base | Treated | Difference | 95% CI | n |
|---|---|---|---|---|---|---|
| wrong candidate: `wrong_wrong - wrong_keywords` | SUPPORTED | 0.07 | 0.22 | +0.14 | [0.06, 0.23] | 97 |
| wrong candidate: `wrong_wrong - wrong_keywords` | REFUTED | 0.76 | 0.63 | -0.13 | [-0.22, -0.05] | 97 |
| correct answer: `true_true - true_keywords` | SUPPORTED | 0.11 | 0.52 | +0.40 | [0.30, 0.51] | 97 |
| correct answer: `true_true - true_keywords` | REFUTED | 0.81 | 0.44 | -0.37 | [-0.47, -0.27] | 97 |
| documents: `wrong_wrong_kwsnip - wrong_keywords` | SUPPORTED | 0.07 | 0.14 | +0.07 | [0.02, 0.13] | 97 |
| documents: `wrong_wrong_kwsnip - wrong_keywords` | REFUTED | 0.76 | 0.70 | -0.06 | [-0.13, 0.01] | 97 |
| snippets: `wrong_wrong - wrong_wrong_kwsnip` | SUPPORTED | 0.14 | 0.22 | +0.07 | [0.01, 0.13] | 97 |
| snippets: `wrong_wrong - wrong_wrong_kwsnip` | REFUTED | 0.70 | 0.63 | -0.07 | [-0.14, 0.00] | 97 |

Source: `results/reader_summary_dev.csv`. Condition names are `<proposed answer>_<query whose results were read>`.

**Limitations.**
- Development questions only; these results guided design choices and are not confirmatory.
- The reader often answers REFUTED for correct answers when the results do not contain them, so REFUTED often
  means "not shown" rather than "shown wrong".
- Whether gold documents actually refute the wrong candidate is our inference, not a dataset label; it will be
  checked with manual labels before it is relied on.
- One retriever (BM25) and one small reader model.

## Next steps

1. Manual labels for the top `q_wrong` documents and for gold documents (do they refute the candidate?).
2. Freeze the pipeline and run the held-out test questions.
3. A dense retriever (H3).

## Repository layout

```
notebooks/01_pilot.ipynb   the full pilot, with outputs and a dated summary
scripts/                   corpus index builder and resumable local LLM runner
results/                   saved per-question results and summaries (development questions)
LOG.md                     dated log of what was run, found and decided
```

## Reproducing

1. Create a conda environment with Python 3.11 and `pip install -r requirements.txt`.
2. Download `Tevatron/browsecomp-plus` (revision `144cff8e35b5eaef7e526346aa60774a9deb941f`) and
   `Tevatron/browsecomp-plus-corpus` (revision `b27b02bc3e45511b8b82a13e6f90ce761df726f6`) from Hugging Face into
   `data/browsecomp-plus/`.
3. Build the corpus index with `scripts/build_corpus_index.py` (peak memory about 8.5 GB).
4. Download `Qwen/Qwen3-4B-GGUF` (`Qwen3-4B-Q4_K_M.gguf`) and run the notebook. Reader runs are slow on CPU
   (about 14.5 hours for 388 prompts); the notebook has `RUN_*` switches for slow parts.

## Data policy

No dataset content is stored in this repository. BrowseComp-Plus is distributed obfuscated to keep it out of model
training data; the notebook de-obfuscates only into the gitignored `data/` directory, and committed outputs contain
only aggregates, query IDs and document IDs, never question, answer or document text.

## Reference

Chen et al. *BrowseComp-Plus: A More Fair and Transparent Evaluation Benchmark of Deep-Research Agent.*
arXiv:2508.06600.

## License

Code is released under the MIT License (see `LICENSE`).
