import os
import requests
from pydantic import BaseModel
import google.auth.transport.requests
from .utils import get_gcp_endpoint_paths

class InferenceRequest(BaseModel):
    node: str = "gcp-endpoint"
    stream: bool = False
    query: str = None
    model: str
    collect_kpis: bool = False
    max_new_tokens: int = 512

def get_connexion_params(node: str, endpoint: dict, project: dict, region: str):
    session = requests.Session()
    url = None
    if "gcp" in node:
        base_url = get_gcp_endpoint_paths(endpoint, project, region=region)
        credentials, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        
        session.headers.update({
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        })
        url = f"{base_url}/{endpoint['name']}"
    elif node == "claude":
        ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        session.headers.update({
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        })
        url = "https://api.anthropic.com/v1/messages"
        ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        session.headers.update({
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        })
    return url, session

def get_payload(req: InferenceRequest):
    if req.node == "gcp-triton":
        collect_kpis = {"name": "return_perf_metrics", "shape": [1, 1], "datatype": "BOOL", "data": [True]}
        inputs_dict = {
            "inputs": [
                {"name": "text_input", "shape": [1, 1], "datatype": "BYTES", "data": [req.query]},
                {"name": "max_tokens", "shape": [1, 1], "datatype": "INT32", "data": [req.max_new_tokens]},
                {"name": "exclude_input_in_output", "shape": [1, 1], "datatype": "BOOL", "data": [True]},
                {"name": "return_log_probs", "shape": [1,1], "datatype": "BOOL", "data": [True]},
                #{"name": "return_kv_cache_reuse_stats", "shape": [1, 1], "datatype": "BOOL", "data": [False]},
                #{"name": "stop", "shape": [1, 1], "datatype": "BOOL", "data": [False]},
                {"name": "stream", "shape": [1, 1], "datatype": "BOOL", "data": [False]},
                ]
        }
        if req.collect_kpis:
            inputs_dict["inputs"].append(collect_kpis)
        payload = inputs_dict
    else:
        payload = {
            "instances": [{"text": req.query}],
            "stream": req.stream,
            "collect_kpis": req.collect_kpis
        }
    return payload
