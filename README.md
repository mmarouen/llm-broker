# 🧠 llm-broker

Internal orchestration layer for LLM routing, multi-provider inference, and load testing. Sits between consumers and inference backends — no model weights, no inference logic.
Current implementation runs for GCP endpoint or a SaaS LLM provider.

---

## Overview

`llm-broker` is the central nervous system of the LLM stack. It abstracts over multiple inference providers, handles request routing, runs stress tests, and collects KPIs.

It talks to:
- **[`llm-multiserve`](https://github.com/mmarouen/llm-multiserve)** — self-hosted models on GCP (vLLM, PyTorch, TensorRT-LLM)
- **Anthropic (Claude)** — managed API

It does **not** hold any inference logic. All model execution is delegated downstream.

---

## Architecture

```
llm-platform/
├── app.py                    # FastAPI entrypoint
├── config/config.py          # Model registry + provider config
├── src/                      
│   ├── api.py                # build payload + collects inference url
│   ├── metrics.py            # computes aggregated metrics: latency, trhoughput, ttft...
│   ├── test.py               # stress test logic
│   ├── utils.py              # some tooling
│   └── prompts.py            # prompt bank
├── Dockerfile                # 
├── requirements.txt          # runtime + gcp dependencies
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
Route an inference request to the appropriate backend for completions. Supports streaming.

**Request:**
```json
{
  "node": "gcp-endpoint",
  "model": "gcp-europe-west3",
  "prompt": "Summarize the following...",
  "stream": true
}
```

- If `stream: true`, returns a `text/event-stream` response.
- The `node` field determines which provider and connection params to use, can either be `claude` or `gcp-endpoint`
- The `model` field depens on `node`: 
    - if `node` is `gcp-endpoint`: looked up in `config['models']` to resolve the downstream endpoint.
    It can be one of `llama-3.2-pytorch`, `llama-3.2-vllm`, `llama-3.2-trtllm`
    - if `node` is `claude`: model is `claude-sonnet-4-6`

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

As of now, the repo is unusable without substantial modification to the node retrieval and storage paths because most endpoint information and model ids are sensitive information.
Config file isnt uploaded along with the repository

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

[LICENSE](LICENSE)