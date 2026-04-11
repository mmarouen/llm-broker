import json
import os
import yaml
import requests
import google.auth
import google.auth.transport.requests

with open(os.path.join('config', 'config.yaml'), 'r') as file:
    config = yaml.safe_load(file)

with open(os.path.join('config', '.env.yaml'), 'r') as file:
    project = yaml.safe_load(file)['project']

PROJECT_ID = project['id']
PROJECT_NR=project['number']
IMAGE_NAME = config['backend']['image']['image-name']
MODEL = 'llama-3.2-trtllm'
TASK = 'stress-test'
STREAM = False
COLLECT_KPIS = True
NODE = 'gcp-endpoint'
REGION = project['region']

def stream_response(response):
    line_idx = 0
    for line in response.iter_lines():
        if line:
            line_idx +=1
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                dict_str = decoded_line.replace("data: ", "").strip()
                if 'ttft' in decoded_line:
                    ttft = json.loads(dict_str)['meta']['ttft']
                    print(f'ttft {ttft}')
                elif 'text' in decoded_line:
                    content = json.loads(dict_str)
                    print(content['text'], end="", flush=True)

url = f'https://{IMAGE_NAME}-{PROJECT_NR}.{REGION}.run.app'
credentials, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

test_url = f'{url}/run_test'
inference_url = f'{url}/completions'
headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json"
}

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json"
})

if __name__ == "__main__":

    test_data = {
        "node": NODE, #claude, gcp-endpoint, gcp-triton
        "stream": False,
        "collect_kpis": True,
        "model": MODEL,
        "max_new_tokens": config['models'][MODEL]['inference'].get('max_new_tokens', 512)
    }
    inference_data = {
        'node': NODE,
        "stream": STREAM,
        "query": "Write a short scientifically accurate story about a middle aged man 2000 years BC daily life",
        "collect_kpis": COLLECT_KPIS,
        "model": MODEL,
        "max_new_tokens": config['models'][MODEL]['inference'].get('max_new_tokens', 512)
    }
    data = inference_data if TASK == 'inference' else test_data
    url = inference_url if TASK == 'inference' else test_url
    response = session.post(url, json=data)
    if not STREAM:
        text = response.json()
        print(text)
    else:
        stream_response(response)