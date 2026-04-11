from concurrent.futures import ThreadPoolExecutor
import time
import uuid
import json
import random
from .metrics import StageReport
from .utils import submit_request, summarize
from .api import get_payload, InferenceRequest

def worker_loop(stop_time, prompt_bank, http_session, url, metrics, model, request: InferenceRequest):
    while time.time() < stop_time:
        base_prompt = random.choice(prompt_bank)
        # 2. Add a unique ID to ensure no cache hits
        request_id = uuid.uuid4()
        unique_prompt = f"[Request ID: {request_id}]: {base_prompt} [Request ID: {request_id}]"
        data = None
        request.query = unique_prompt
        request.collect_kpis = True
        if "gcp" in request.node:
            data = get_payload(req=request)
        elif request.node == "claude":
            data = {
                "model": model,
                "max_tokens": request.max_new_tokens,
                "messages": [{"role": "user", "content": unique_prompt}]
            }
        latency = -1
        ttft = -1
        output_tokens = -1
        input_tokens = -1
        tps = -1
        start_time = time.time()
        try:
            if request.node == "gcp-endpoint":
                response_iter = submit_request(data, url=url, stream=request.stream, session=http_session)
                result = next(response_iter)
                latency = time.time() - start_time
                pred = result["predictions"][0]
                ttft = pred.get("ttft", -1)
                output_tokens = pred.get("output_tokens", -1)
                input_tokens = pred.get("input_tokens", -1)
                tps = pred.get("tps", 0)
            elif request.node == "gcp-triton":
                response_iter = submit_request(data, url=url, stream=request.stream, session=http_session)
                '''
                total_output_tokens = 0
                for chunk in response_iter:
                    try:
                        parsed = json.loads(chunk.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    ttft = time.time() - start_time
                    outputs = parsed.get("outputs", [])
                    for out in outputs:
                        if out["name"] == "output_log_probs":
                            total_output_tokens += out["shape"][-1]
                '''
                json_result = next(response_iter)["outputs"]
                latency = time.time() - start_time
                output_token_ = next((d for d in json_result if d["name"] == "output_log_probs"), None)
                output_tokens = output_token_["shape"][-1]
                tps = output_tokens / latency if latency > 0 and output_tokens > 0 else -1
            elif request.node == "claude":
                response = http_session.post(url, json=data)
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 2.0))
                    print(f'retrying request after {retry_after}')
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                body = response.json()
                latency = time.time() - start_time
                input_tokens = body.get("usage", {}).get("input_tokens", -1)
                output_tokens = body.get("usage", {}).get("output_tokens", -1)
                tps = output_tokens / latency if latency > 0 and output_tokens > 0 else -1

        except Exception as e:
            print(f"Request failed: {e}")
        metrics.append({
            "latency": latency,
            "ttft": ttft,
            "output_tokens": output_tokens,
            "input_tokens": input_tokens,
            "tps": tps
        })

def run_stress_test(
        stop_time,
        concurrency,
        duration,
        prompt_bank,
        session,
        url,
        model,
        request
        ) -> StageReport:
    metrics = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for _ in range(concurrency):
            executor.submit(
                worker_loop,
                stop_time,
                prompt_bank,
                session,
                url,
                metrics,
                model,
                request
            )
        # Wait for the duration of the stage
        while time.time() < stop_time:
            time.sleep(1)
    return summarize(duration, metrics)

