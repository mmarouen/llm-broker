import os
import yaml
import subprocess

if __name__ == "__main__":

    with open(os.path.join('config', 'config.yaml'), 'r') as file:
        config = yaml.safe_load(file)
    with open(os.path.join('config', '.env.yaml'), 'r') as file:
        project = yaml.safe_load(file)['project']

    image_config = config['backend']['image']
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    url = f"{project['region']}-docker.pkg.dev/{project['id']}/{image_config['repository-name']}/{image_config['image-name']}:latest"
    compute = config['backend']['compute']
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    shell_string = f'gcloud run deploy {image_config["image-name"]} \
--image {url} \
--source {project_root} \
--set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest" \
--region {project["region"]} \
--allow-unauthenticated \
--platform managed \
--timeout {compute["timeout"]} \
--cpu {compute["cpu"]} \
--memory {compute["ram"]}'
    try:
        subprocess.run(shell_string, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred in {__file__}: {e}")
        exit(1)
