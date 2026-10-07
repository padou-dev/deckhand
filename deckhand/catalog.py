from pathlib import Path

import yaml

catalog_folder = Path("catalog")

for path in sorted(catalog_folder.glob("*.yaml")):
    with open(path) as file:
        app = yaml.safe_load(file)
    print(f"{app['name']} ({app['category']}) runs on port {app['web_port']}")