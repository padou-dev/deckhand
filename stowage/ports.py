import socket


def host_ports(entry):
    ports = []
    for service in entry["services"].values():
        if service.get("network_mode") == "host" and entry.get("web_port"):
            ports.append(entry["web_port"])
        for mapping in service.get("ports", []):
            if mapping.endswith("/udp"):
                continue
            parts = mapping.split("/")[0].split(":")
            ports.append(int(parts[-2]))
    return ports


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def busy_ports(entry):
    busy = []
    for port in host_ports(entry):
        if port_in_use(port):
            busy.append(port)
    return busy