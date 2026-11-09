# AegisSOC-X Enterprise (Portfolio Prototype)

A reproducible, human-reviewed security investigation prototype combining:
- Random Forest detection of network flows (synthetic smoke test or CIC-IDS2017 CSV)
- Optional PyTorch MLP model comparison
- FastAPI prediction and SQLite case management
- LangGraph investigation steps with optional Ollama-generated narrative
- Analyst approval, audit trail and Streamlit dashboard

**Not production ready.** The default dataset is synthetic and has no cybersecurity validity.
The real-data path uses historical CIC-IDS2017 flow records; its predictions must not be
treated as validated modern enterprise threat detection. The LLM never executes remediation.

## Full build guide
[Complete walkthrough with commands and screenshot locations](docs/COMPLETE_WALKTHROUGH.md)

## Quickstart (WSL Ubuntu)
```bash
uv sync --group dev
uv run python -m aegissoc.train
uv run pytest -q
uv run uvicorn aegissoc.api:app --reload
# another terminal:
uv run streamlit run src/aegissoc/dashboard.py
```
Open http://127.0.0.1:8000/docs and http://localhost:8501.

## Real data
Download MachineLearningCSV files from https://www.unb.ca/cic/datasets/ids-2017.html
and place one CSV at `data/raw/flows.csv` (not committed).
```bash
uv run python -m aegissoc.train --csv data/raw/flows.csv
```
This uses a random stratified holdout **only for an initial baseline**. For publishable
claims, implement a day/session/group holdout and test for temporal leakage.

## Neural network comparison
```bash
uv sync --group dev --extra deep-learning
uv run python -m aegissoc.neural --csv data/raw/flows.csv
```
Use `uv run python -m aegissoc.neural` for a synthetic demonstration.

## Ollama optional
Install Ollama, pull a compatible model, and run it locally. The graph works without it,
using a deterministic report. Set `USE_OLLAMA=1` when running the API to enable narrative
generation. LLM text is untrusted and requires human review.

## Tests / quality
```bash
uv run pytest -q
uv run ruff check .
```

## Security limitations
- Demo API has no authentication: bind to localhost only.
- No autonomous containment; all case decisions are human-entered.
- Model and dataset artifacts are local, not published.
- Real production deployments need SSO/RBAC, TLS, secrets management, database migrations,
  monitoring, adversarial testing, stronger dataset evaluation and review of legal requirements.

## Project documentation
See docs/BUILD.md, docs/EVALUATION.md, docs/ARCHITECTURE.md and docs/DEMO.md.

## Project Demonstration

### Machine Learning Detection
![ML results](docs/screenshots/04_real_ml.png)

### Neural Network Training
![PyTorch training](docs/screenshots/05_neural_epochs.png)

### Security API
![API documentation](docs/screenshots/07_api_docs.png)

### Agentic Investigation
![Investigation](docs/screenshots/10_agent_investigation.png)

### Analyst Dashboard
![Dashboard](docs/screenshots/12_dashboard.png)