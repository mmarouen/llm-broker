# 🧠 llm-broker

Internal orchestration layer for LLM routing, multi-provider inference, and load testing. Sits between consumers and inference backends — no model weights, no inference logic.

---

## Overview

`llm-broker` is the central nervous system of the LLM stack. It abstracts over multiple inference providers, handles request routing, runs stress tests, and collects KPIs.

It talks to:
- **[`llm-multiserve`](https://github.com/mmarouen/llm-multiserve)** — self-hosted models on GCP (vLLM, PyTorch, TensorRT-LLM)
- **Anthropic (Claude)** — managed API
- **OpenAI (GPT)** — managed API

It does **not** hold any inference logic. All model execution is delegated downstream.

---

## Architecture

```
llm-platform/
├── app.py                    # FastAPI entrypoint
├── config.py                 # Model registry + provider config
├── clients/                  # One module per downstream provider
│   ├── gateway.py            # → inference-gateway (GCP)
│   ├── anthropic.py          # → Claude API
│   └── openai.py             # → GPT API
├── routing/                  # Provider selection logic
├── stress/                   # Load testing (stages, runners)
│   ├── runner.py             # run_stress_test logic
│   └── prompts.py            # Prompt banks (e.g. LISO_PROMPTS)
├── kpis/                     # KPI computation + metrics models
├── storage/                  # GCS upload helpers
└── requirements/
    ├── base.txt
    └── dev.txt
```

---

## API

### `GET /`
Health check.

```json
{ "status": "ok" }
```

---

### `POST /completions`
Route an inference request to the appropriate backend. Supports streaming.

**Request:**
```json
{
  "model": "mistral-7b",
  "node": "gcp-europe-west3",
  "prompt": "Summarize the following...",
  "stream": true
}
```

- If `stream: true`, returns a `text/event-stream` response.
- The `node` field determines which provider and connection params to use.
- The `model` field is looked up in `config['models']` to resolve the downstream endpoint.

---

### `POST /run_test`
Run a multi-stage stress test against a target node and model, then upload results to GCS.

**Request:** same schema as `/completions`.

**Stages** (defined in `app.py`):

| Stage | Concurrency | Duration |
|---|---|---|
| Baseline | 1 | 30s |
| Low Load | 2 | 30s |
| Medium Load | 5 | 60s |
| Heavy Stress | 10 | 60s |
| — | 20 | 120s |
| — | 40 | 240s |

Results are uploaded to the GCS bucket configured in `config['models'][model]['storage']`.

---

## Configuration

Models and endpoints are defined in `config.py` (or loaded from a config file). Each model entry resolves:

```python
config['models']['mistral-7b'] = {
    "endpoint": "projects/.../endpoints/...",
    "storage": {
        "bucket": "gs://your-bucket/results"
    }
}
```

The `node` field in requests controls routing:
- Nodes containing `"gcp"` → routed to `inference-gateway`, using the configured model name
- Other nodes → routed to Claude (`CLAUDE_MODEL`)

---

## Region

Currently hardcoded to `europe-west3`. Configurable via `REGION` in `app.py`.

---

## Getting Started

> _TODO_

---

## Deployment

> _TODO: Cloud Run / GCP endpoint deployment, env vars, auth._

---

## KPIs & Metrics

> _TODO: Document the metrics model (`stage_result.model_dump()`), what's tracked, and how results are structured in GCS._

---

## Logging

> _TODO_

---

## Contributing

> _TODO_

---

## License

> _TODO_