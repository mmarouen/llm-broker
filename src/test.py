from concurrent.futures import ThreadPoolExecutor
import time
import uuid
import random
from .metrics import StageReport
from .utils import submit_request, summarize

def worker_loop(stop_time, prompt_bank, stream, http_session, url, metrics, model, backend):
    while time.time() < stop_time:
        base_prompt = random.choice(prompt_bank)
        # 2. Add a unique ID to ensure no cache hits
        request_id = uuid.uuid4()
        unique_prompt = f"[Request ID: {request_id}]: {base_prompt} [Request ID: {request_id}]"
        data = None
        if backend == "gcp_endpoint":
            data = {
                "instances": [{"text": unique_prompt}],
                "stream": stream,
                "collect_kpis": True
            }
        elif backend == "claude":
            data = {
                "model": model,
                "max_tokens": 600,
                "messages": [{"role": "user", "content": unique_prompt}]
            }
        latency = -1
        ttft = -1
        output_tokens = -1
        input_tokens = -1
        tps = -1
        start_time = time.time()
        try:
            if backend == "gcp_endpoint":
                response_iter = submit_request(data, url=url, stream=stream, session=http_session)
                result = next(response_iter)
                latency = time.time() - start_time
                pred = result["predictions"][0]
                ttft = pred.get("ttft", -1)
                output_tokens = pred.get("output_tokens", -1)
                input_tokens = pred.get("input_tokens", -1)
                tps = pred.get("tps", 0)

            elif backend == "claude":
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
        stream,
        session,
        url,
        model,
        backend
        ) -> StageReport:
    metrics = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for _ in range(concurrency):
            executor.submit(
                worker_loop,
                stop_time,
                prompt_bank,
                stream,
                session,
                url,
                metrics,
                model,
                backend
            )
        # Wait for the duration of the stage
        while time.time() < stop_time:
            time.sleep(1)
    return summarize(duration, metrics)

