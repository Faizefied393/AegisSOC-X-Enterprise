# AegisSOC-X: complete build and screenshot walkthrough

This is a **local portfolio prototype**, not a production security system. Implemented: Random Forest pipeline, optional PyTorch MLP, FastAPI/SQLite case workflow, bounded LangGraph evidence report, optional Ollama narrative, Streamlit UI, pytest and CI. Not yet implemented: authentication, independent agent tool selection, XGBoost, MLflow, PostgreSQL, Docker deployment or validated ROI. Build and verify those as upgrades below.

## 0. Prerequisites
Windows 11, VS Code WSL extension, Ubuntu WSL, Python 3.12, Git, uv. Optional Ollama and Docker Desktop WSL integration.
Sources: https://code.visualstudio.com/docs/remote/wsl , https://docs.astral.sh/uv/ , https://docs.docker.com/desktop/features/wsl/

## 1. Extract, open and install (20-40 min)
Download the ZIP to Windows Downloads. In WSL Ubuntu:
```bash
mkdir -p ~/projects && cd ~/projects
# Change the Windows username/path to match your Downloads folder:
cp /mnt/c/Users/<WINDOWS_USERNAME>/Downloads/AegisSOC-X_Enterprise_Complete.zip .
unzip AegisSOC-X_Enterprise_Complete.zip
cd aegissoc-x
code .
uv sync --group dev --python 3.12
uv run python -c "import aegissoc, sklearn, fastapi, langgraph; print('READY')"
python3 --version; git --version; uv --version
uv run pytest -q
uv run ruff check .
```
Learn: reproducible Python environment, packaging, tests and lint.
**Screenshots:** `docs/screenshots/01_setup.png` (VS Code tree + version checks), `docs/screenshots/02_tests.png` (passing tests).

## 2. Train synthetic baseline (15-30 min)
```bash
uv run python -m aegissoc.train
cat artifacts/metrics.json
```
Learn: training/testing, class imbalance, precision, recall, F1, PR-AUC and false-positive rate.
**Screenshot:** `docs/screenshots/03_synthetic_ml.png` (actual training metrics). Synthetic scores are NOT cybersecurity performance.

## 3. Train with real network-flow data (1-3 hours)
Download official CIC-IDS2017 MachineLearningCSV from https://www.unb.ca/cic/datasets/ids-2017.html . Extract one CSV with both benign and attack examples to `data/raw/flows.csv` (do not commit data).
```bash
uv run python -m aegissoc.train --csv data/raw/flows.csv
cat artifacts/metrics.json
```
Learn: data provenance, cleaning, labels, numeric features, leakage. **Caveat:** starter random row split can overestimate performance due to correlated flows. For defensible evaluation, create held-out days/sessions and repeat.
**Screenshot:** `docs/screenshots/04_real_ml.png` (real-data metrics).

## 4. Train PyTorch neural network (1-3 hours)
```bash
uv sync --group dev --extra deep-learning
uv run python -m aegissoc.neural --csv data/raw/flows.csv
cat artifacts/mlp_metrics.json
```
For synthetic test omit `--csv`. Learn: ReLU, logits, weighted loss, AdamW, early stopping, overfitting. Compare models on identical held-out rows for a fair benchmark.
Source: https://pytorch.org/tutorials/
**Screenshots:** `docs/screenshots/05_neural_epochs.png`, `docs/screenshots/06_model_comparison.png`.

## 5. Start FastAPI and test inference (20-40 min)
Terminal A:
```bash
uv run uvicorn aegissoc.api:app --host 127.0.0.1 --reload
```
Open http://127.0.0.1:8000/docs . Terminal B:
```bash
curl http://127.0.0.1:8000/health
uv run python -c 'import json,requests; f=json.load(open("artifacts/metrics.json"))["features"]; r=requests.post("http://127.0.0.1:8000/predict",json={"features":{k:0.0 for k in f}},timeout=20); print(r.status_code,r.json())'
```
All-zero input tests the API only, not real detection. Learn: API schemas, inference, serialization and validation.
Source: https://fastapi.tiangolo.com/tutorial/
**Screenshots:** `docs/screenshots/07_api_docs.png`, `docs/screenshots/08_prediction.png`.

## 6. Create, investigate and review a case (20-40 min)
```bash
curl -X POST http://127.0.0.1:8000/cases -H 'Content-Type: application/json' -d '{"score":0.91,"event":{"id":"demo-001","source":"synthetic","description":"Demo security event"}}'
```
Use the returned case ID (replace 1 if different):
```bash
curl -X POST http://127.0.0.1:8000/cases/1/investigate
curl -X POST http://127.0.0.1:8000/cases/1/review -H 'Content-Type: application/json' -d '{"reviewer":"demo-analyst","decision":"needs_more_evidence"}'
curl http://127.0.0.1:8000/audit
```
The supplied 0.91 is a demo score, not a model prediction. Learn: stateful workflows, evidence, human-in-the-loop and audit.
Source: https://docs.langchain.com/oss/python/langgraph/overview
**Screenshots:** `docs/screenshots/09_agent_report.png`, `docs/screenshots/10_review_audit.png`.

## 7. Optional Ollama narrative (30-60 min + model download)
If Ollama is installed and reachable, run `ollama pull llama3.2`. Restart the API:
```bash
USE_OLLAMA=1 uv run uvicorn aegissoc.api:app --host 127.0.0.1 --reload
```
Create and investigate another case. Learn: LLM grounding, hallucination risk, deterministic fallback. LLM narrative is explicitly unverified.
Source: https://github.com/ollama/ollama
**Screenshot:** `docs/screenshots/11_llm_report.png`.

## 8. Start analyst dashboard (20-40 min)
Keep API running. New terminal:
```bash
uv run streamlit run src/aegissoc/dashboard.py
```
Open http://localhost:8501 . Investigate and review cases and inspect audit events.
Source: https://docs.streamlit.io/
**Screenshot:** `docs/screenshots/12_dashboard.png`.

## 9. ML engineering upgrades (additional development)
- Add reproducible day/session holdout; save split IDs.
- Train XGBoost with `uv add xgboost` on the same holdout.
- Enable MLflow with `uv sync --group dev --extra experiments`; log runs and model artifacts.
- Calibrate thresholds on validation, never test; report confusion matrix, PR-AUC, latency and drift.
Sources: https://scikit-learn.org/stable/modules/cross_validation.html , https://mlflow.org/docs/latest/
**Screenshot after implementation:** `docs/screenshots/13_mlflow_comparison.png`.

## 10. Secure agentic engineering upgrades (additional development)
- Implement read-only tools `get_event`, `search_related_events`, `get_model_explanation`, `lookup_attack_technique`.
- Build bounded LangGraph tool selection, evidence IDs, source-grounded reporting and step limits.
- Implement authentication/RBAC, per-tool permissions, audit logs and prompt-injection tests.
- Keep current unauthenticated API on localhost; never expose it publicly.
Sources: https://docs.langchain.com/oss/python/langgraph/overview , https://genai.owasp.org/
**Screenshots after implementation:** `docs/screenshots/14_agent_trace.png`, `docs/screenshots/15_authorization_tests.png`.

## 11. Business / infrastructure upgrades (additional development)
- Add PostgreSQL + migrations, Docker Compose, monitoring and CI.
- Measure manual vs assisted review times on the same labeled cases; record sample size, accuracy, latency, cost and reviewer corrections. Never invent savings.
Sources: https://docs.docker.com/compose/ , https://docs.github.com/en/actions
**Screenshots after implementation:** `docs/screenshots/16_business_metrics.png`, `docs/screenshots/17_deployment.png`.

## 12. Publish and present (30-60 min)
```bash
uv run pytest -q
uv run ruff check .
git init
git branch -M main
git add .
git diff --cached --stat
git diff --cached
git commit -m 'Build AegisSOC-X ML and AI investigation prototype'
```
Inspect all staged files for secrets and sensitive data before committing. Publish via VS Code Source Control. Include 5-7 best screenshots in README with Markdown, e.g. `![Analyst dashboard](docs/screenshots/12_dashboard.png)`. Keep detailed screenshots in `docs/`.
**Screenshot after publishing:** `docs/screenshots/18_github_ci.png`.

## Five-minute demo
1. Business problem and architecture (30 sec)
2. Dataset provenance, ML/NN metrics and limitations (60 sec)
3. FastAPI prediction (45 sec)
4. Case investigation and agent evidence (60 sec)
5. Human review and dashboard audit trail (45 sec)
6. Security tests, operational evaluation and future work (60 sec)

## Evidence and documentation standard
At every stage: **run -> verify -> screenshot -> document -> commit**. Put actual results and limitations in `docs/EVALUATION.md`. Do not publish credentials, private data, access tokens, or raw datasets. Do not call unimplemented upgrades finished.
