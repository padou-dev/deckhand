from pathlib import Path

import yaml
import subprocess
import secrets
import socket
import os
import shutil

STACKS_FOLDER = Path.home() / "stowage_stacks"

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
    if value == "uid":
        return str(os.getuid())
    if value == "gid":
        return str(os.getgid())
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

    for service in entry["services"].values():
        for volume in service.get("volumes", []):
            host_path = volume.split(":")[0]
            if host_path.startswith("./"):
                (stack_folder / host_path).mkdir(parents=True, exist_ok=True)

    compose = {"services": entry["services"]}
    with open(compose_file, "w") as file:
        yaml.safe_dump(compose, file, sort_keys=False)

    if "env" in entry:
        env_file = stack_folder / ".env"
        env_file.write_text(build_env(entry))
        env_file.chmod(0o600)
        
    return compose_file

def start_stack(app_id, should_cancel):
    process = subprocess.Popen(
        ["docker", "compose", "up", "-d"],
        cwd=STACKS_FOLDER / app_id,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    while True:
        try:
            _, errors = process.communicate(timeout=0.5)
        except subprocess.TimeoutExpired:
            if should_cancel():
                process.terminate()
                process.communicate()
                return "cancelled", ""
            continue
        if process.returncode == 0:
            return "ok", ""
        return "failed", errors.strip()

def remove_stack(app_id):
    stack_folder = STACKS_FOLDER / app_id
    subprocess.run(
        ["docker", "compose", "down"],
        cwd=stack_folder,
        capture_output=True,
        start_new_session=True,
    )
    try:
        shutil.rmtree(stack_folder)
        return True
    except OSError:
        return False

def stack_exists(app_id):
    return (STACKS_FOLDER / app_id / "docker-compose.yml").exists()