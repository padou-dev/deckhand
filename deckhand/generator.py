from pathlib import Path

import yaml

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