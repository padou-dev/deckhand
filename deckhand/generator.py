from pathlib import Path

import yaml
import subprocess

STACKS_FOLDER = Path.home() / "deckhand_stacks"


def write_stack(entry):
    stack_folder = STACKS_FOLDER / entry["id"]
    compose_file = stack_folder / "docker-compose.yml"

    if compose_file.exists():
        return None

    stack_folder.mkdir(parents=True, exist_ok=True)

    compose = {"services": entry["services"]}
    with open(compose_file, "w") as file:
        yaml.safe_dump(compose, file, sort_keys=False)

    return compose_file

def start_stack(app_id):
    stack_folder = STACKS_FOLDER / app_id
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=stack_folder,
        capture_output=True,
        text=True,
    )
    return result