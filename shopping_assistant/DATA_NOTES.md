# Data inspection notes

Inspection date: 2026-10-18. The repository and nearby `jarvis-assistant` directory had no catalogue, policy document, questions, or model cache. Python 3.13.7 was available, but pandas, numpy, rank_bm25, rapidfuzz, sentence-transformers, transformers, torch, gradio, pytest, and matplotlib were absent. Network use is not required by this implementation.

Accordingly, the checked-in CSV and policy are labelled synthetic demo inputs. The demo vocabulary sizes are computed at load time and printed by `ingest.py`. CSV/JSON/JSONL load with standard-library code; Parquet uses an optional pandas adapter. IDs use the provided ID column when available and otherwise deterministic P00001-style IDs. Attribute dictionaries and flattened columns are supported. Policy sections are split by headings and paragraphs. No model files were found, so parsing is rules-only and local hashed-token vectors are the offline dense fallback.

Assumption: an actual deployment supplies the promised catalogue and policy through `TRUSTCART_CATALOG` and `TRUSTCART_POLICY`; no synthetic fact should be presented as an actual merchant fact.
