# End-to-end build checklist

1. Install WSL Ubuntu, Python 3.12, Git, uv and VS Code WSL extension.
2. `uv sync --group dev`
3. `uv run python -m aegissoc.train` — synthetic pipeline smoke test.
4. `uv run pytest -q && uv run ruff check .`
5. Download official CIC-IDS2017 MachineLearningCSV, place a CSV in `data/raw/flows.csv`.
6. `uv run python -m aegissoc.train --csv data/raw/flows.csv`
7. Read `artifacts/metrics.json` and inspect precision/recall/F1 and confusion matrix.
8. `uv sync --group dev --extra deep-learning` then run neural model.
9. Start API `uv run uvicorn aegissoc.api:app --reload`.
10. Open `/docs`, create prediction with `/predict`, then create case with `/cases`.
11. POST `/cases/{id}/investigate`, inspect evidence, then POST `/cases/{id}/review`.
12. Start dashboard `uv run streamlit run src/aegissoc/dashboard.py`.
13. Record results and limitations in `docs/EVALUATION.md`.
14. `git status`, check for secrets/data, commit, and publish your own GitHub repository.

Never describe synthetic smoke-test results as actual cybersecurity performance.
