from google.cloud import storage
import json
import datetime
import numpy as np
from .metrics import StageReport

def upload_results(results, gs_bucket, gs_relative_path='stress-tests'):

    client = storage.Client()
    bucket = client.bucket(gs_bucket)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    blob = bucket.blob(f"{gs_relative_path}/run_{timestamp}.json")

    blob.upload_from_string(
        json.dumps(results, indent=2),
        content_type="application/json"
    )

def get_gcp_endpoint_paths(endpoint: dict, number: str, region: str, project_id: str):
    endpoint_path = f"{endpoint['id']}.{region}-{number}.prediction.vertexai.goog" if endpoint['is-dedicated'] else f"{region}-aiplatform.googleapis.com"
    resource_path = f"projects/{project_id}/locations/{region}/endpoints/{endpoint['id']}"
    return f"https://{endpoint_path}/v1/{resource_path}/invoke/predict"

def submit_request(payload_dict, url, session, stream=True):
    response = session.post(url, json=payload_dict, stream=stream, timeout=(5.0, 60.0))

    if response.status_code != 200:
        raise Exception(f"Request failed with status {response.status_code}: {response.text}")
    if stream:
        # Iterate over the raw HTTP bytes as they arrive
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                yield line
    else:
        yield response.json()

def summarize(stage_duration, metrics) -> StageReport:

    if not metrics:
        print('No metrics found')
        return

    latencies = [m["latency"] for m in metrics if m["latency"] != -1]
    ttfts = [m["ttft"] for m in metrics if m["ttft"] != -1]
    output_tokens = [m["output_tokens"] for m in metrics if m["output_tokens"] != -1]
    input_tokens = [m["input_tokens"] for m in metrics if m["input_tokens"] != -1]
    total_tokens = sum([m["output_tokens"] for m in metrics if m["output_tokens"] != -1])

    system_tps = total_tokens / stage_duration
    report = StageReport()
    report.n_requests_gross = len(metrics)
    report.n_requests = len(latencies)
    if report.n_requests >= 1 :
        report.total_tokens = total_tokens
        report.throughput = system_tps
        report.ttft_p50 = float(np.median(ttfts)) if ttfts else -1
        report.ttft_p95 = sorted(ttfts)[int(len(ttfts) * 0.95)] if ttfts else -1
        report.user_latency_p50 = float(np.median(latencies))
        report.user_latency_p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        report.output_tokens_p50 = int(np.median(output_tokens)) if output_tokens else -1
        report.output_tokens_p95 = sorted(output_tokens)[int(len(output_tokens) * 0.95)] if output_tokens else -1
        report.input_tokens_p50 = int(np.median(input_tokens)) if input_tokens else -1
        report.input_tokens_p95 = sorted(input_tokens)[int(len(input_tokens) * 0.95)] if input_tokens else -1
    return report