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
REGION = project['region']
IMAGE_NAME = config['backend']['image']['image-name']

url = f'https://{IMAGE_NAME}-{PROJECT_NR}.{REGION}.run.app'
credentials, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

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
    test_url = f'{url}/run_test'
    data = {
        "node": "claude", #claude, gcp_endpoint
        "stream": False,
        "trace": False
    }
    response = session.post(test_url, json=data)
    print(response.status_code)
    print(response.text)