from pathlib import Path

import yaml
import subprocess
import secrets

STACKS_FOLDER = Path.home() / "deckhand_stacks"

def build_env(entry):
    lines = []
    for name, value in entry.get("env", {}).items():
        if value == "generate":
            value = secrets.token_urlsafe(24)
        lines.append(f"{name}={value}")
    return "\n".join(lines) + "\n"

def write_stack(entry):
    stack_folder = STACKS_FOLDER / entry["id"]
    compose_file = stack_folder / "docker-compose.yml"

    if compose_file.exists():
        return None

    stack_folder.mkdir(parents=True, exist_ok=True)

    compose = {"services": entry["services"]}
    with open(compose_file, "w") as file:
        yaml.safe_dump(compose, file, sort_keys=False)

    if "env" in entry:
        env_file = stack_folder / ".env"
        env_file.write_text(build_env(entry))
        env_file.chmod(0o600)
        
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