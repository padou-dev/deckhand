from pathlib import Path

import yaml
import subprocess
import secrets
import socket

STACKS_FOLDER = Path.home() / "deckhand_stacks"

def detect_host_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("1.1.1.1", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    
def detect_timezone():
    localtime = Path("/etc/localtime").resolve()
    if "zoneinfo" in localtime.parts:
        index = localtime.parts.index("zoneinfo")
        return "/".join(localtime.parts[index + 1:])
    return "UTC"

def resolve_value(value):
    if value == "generate":
        return secrets.token_urlsafe(24)
    if value == "timezone":
        return detect_timezone()
    if value == "host_ip":
        return detect_host_ip()
    return value

def build_env(entry):
    lines = []
    for name, value in entry.get("env", {}).items():
        lines.append(f"{name}={resolve_value(value)}")
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

def stack_exists(app_id):
    return (STACKS_FOLDER / app_id / "docker-compose.yml").exists()