## 2026-11-04

**Run.** Inspected `slivovitz-raman` read-only and recorded its code and git conventions in `CLAUDE.md`. Initialized git and created the private GitHub repository `ognjenmark/retrieval-confirmation-bias`. Created the conda environment `retrieval-bias` (Python 3.11.18; pandas 3.1.0, numpy 2.4.6, datasets 5.1.0, huggingface_hub 2.4.0, bm25s 0.3.16, jupyter). Downloaded the obfuscated BrowseComp-Plus parquet files into `data/browsecomp-plus/`: `Tevatron/browsecomp-plus` at revision `144cff8e35b5eaef7e526346aa60774a9deb941f` and `Tevatron/browsecomp-plus-corpus` at revision `b27b02bc3e45511b8b82a13e6f90ce761df726f6`.

**Found.** Parquet metadata reports 830 rows in the queries dataset and 100195 rows in the corpus, matching the dataset cards. No data was de-obfuscated and no results were computed.

**Decided.** `CLAUDE.md` and other local Claude files are excluded through `.git/info/exclude`, as in `slivovitz-raman`. The unmerged `harness` branch of `slivovitz-raman` is ignored as a source of conventions. `notebooks/01_pilot.ipynb` was started afterwards, as logged below.
