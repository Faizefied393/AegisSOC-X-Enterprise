setup:
	uv sync --group dev
train:
	uv run python -m aegissoc.train
test:
	uv run pytest -q
lint:
	uv run ruff check .
api:
	uv run uvicorn aegissoc.api:app --reload
dashboard:
	uv run streamlit run src/aegissoc/dashboard.py
