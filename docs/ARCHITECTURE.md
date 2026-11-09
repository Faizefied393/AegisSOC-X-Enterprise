# Architecture

CSV/synthetic generator -> cleaning and feature schema -> RandomForest artifact
-> FastAPI /predict -> case in SQLite -> LangGraph (triage -> evidence -> report)
-> analyst review endpoint -> audit log -> Streamlit dashboard.

Agent graph is deliberately bounded: no shell access, no external browsing,
no destructive actions. Optional Ollama generates a narrative; deterministic
facts and model score are kept separate. Human review is mandatory.
