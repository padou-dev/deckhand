import yaml
with open("catalog/uptime_kuma.yaml") as file:
    app = yaml.safe_load(file)

print(app)
print(f"{app['name']} ({app['category']}) runs on port {app['web_port']}")
print(app["services"]["uptime_kuma"]["image"])