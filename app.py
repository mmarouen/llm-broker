import time
import os
import uvicorn
import yaml
import json
import sys
import logging
from fastapi.responses import StreamingResponse
from fastapi import FastAPI
from src import (upload_results, run_stress_test,
                 LISO_PROMPTS, get_connexion_params,
                 submit_request, InferenceRequest,
                 get_payload
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

with open(os.path.join('config', 'config.yaml'), 'r') as file:
    config = yaml.safe_load(file)
with open(os.path.join('config', '.env.yaml'), 'r') as file:
    project = yaml.safe_load(file)['project']

CLAUDE_MODEL = 'claude-sonnet-4-6'

STAGES = [
    (1, 30),   # Baseline
    (2, 30),   # Low Load
    (5, 60),  # Medium Load
    (10, 60),  # Heavy Stress
    (20, 120),
    (40, 240),
]

#STAGES = [
#    (1, 5)   # Baseline
#]

REGION = 'europe-west3'
app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/completions")
def completions(req: InferenceRequest):
    print(f'Received request {req}')
    endpoint = config['models'][req.model]['endpoint']
    url, session = get_connexion_params(req.node, endpoint=endpoint, project=project, region=REGION)
    payload = get_payload(req)
    generator = submit_request(payload, url=url, stream=req.stream, session=session)
    if req.stream:
        return StreamingResponse(generator, media_type="text/event-stream")
    else:
        return next(generator)

@app.post("/run_test")
def run_test(req: InferenceRequest):

    endpoint = config['models'][req.model]['endpoint']
    storage = config['models'][req.model]['storage']
    url, session = get_connexion_params(req.node, endpoint=endpoint, project=project, region=REGION)
    print(f'url {url}')
    #logging.info(f'Querying node {req.node}: {url}')
    MODEL = req.model if "gcp" in req.node else CLAUDE_MODEL
    results = []
    for concurrency, duration in STAGES:
        logging.info(f"\n--- Stage: {concurrency} users for {duration}s ---")
        stop_time = time.time() + duration
        stage_result = None
        stage_result = run_stress_test(
                stop_time=stop_time,
                concurrency=concurrency,
                duration=duration,
                prompt_bank=LISO_PROMPTS,
                session=session,
                url=url,
                model=MODEL,
                request=req)
        record = {
            "model_name": MODEL,
            "node": req.node,
            "concurrency": concurrency,
            "duration": duration,
            "metrics": stage_result.model_dump()
        }

        logging.info(f"Stress test log {json.dumps(record)}")
        results.append(record)
    upload_results(results=results, gs_bucket=storage['bucket'])
    logging.info(f"Results uploaded to gcp")
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)