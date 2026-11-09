from aegissoc.agent import investigate
from aegissoc.data import load_flows
from aegissoc.train import train


def test_synthetic_data():
    x, y, source = load_flows()
    assert x.shape == (3000, 20)
    assert set(y.unique()) == {0, 1}
    assert source == "synthetic-smoke-test"


def test_training(tmp_path):
    metrics = train(output_dir=str(tmp_path))
    assert (tmp_path / "rf_model.joblib").exists()
    assert 0 <= metrics["precision"] <= 1


def test_investigation_without_llm(monkeypatch):
    monkeypatch.delenv("USE_OLLAMA", raising=False)
    result = investigate({"id": 1, "score": 0.91, "event_json": '{"demo":true}'})
    assert len(result["evidence"]) == 2
    assert "analyst" in result["summary"]
