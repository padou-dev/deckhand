from pathlib import Path

import yaml

CATALOG_FOLDER = Path("catalog")


def load_catalog():
    apps = []
    for path in sorted(CATALOG_FOLDER.glob("*.yaml")):
        with open(path) as file:
            apps.append(yaml.safe_load(file))
    return apps