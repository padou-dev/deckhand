#!/usr/bin/env bash
#
# Deckhand installer: installs Docker and Python, then launches Deckhand.

set -euo pipefail

info() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
error() { printf '\033[1;31mError:\033[0m %s\n' "$1" >&2; exit 1; }

# --- Check the operating system ---
if [[ ! -f /etc/os-release ]]; then
    error "Cannot detect your Linux distribution (/etc/os-release is missing)."
fi

source /etc/os-release

case "$ID" in
    ubuntu|debian)
        info "Detected $PRETTY_NAME"
        ;;
    *)
        error "Unsupported distribution: $ID. Deckhand currently supports Ubuntu and Debian."
        ;;
esac

# --- Work out how to run commands as root ---
if [[ "$EUID" -eq 0 ]]; then
    SUDO=""
elif command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    error "This script needs root access. Run it as root or install sudo."
fi

info "Admin commands will run as: ${SUDO:-root}"

# --- Install Docker ---
install_docker() {
    info "Installing Docker from Docker's official repository..."

    $SUDO apt-get update
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl

    $SUDO install -m 0755 -d /etc/apt/keyrings
    $SUDO curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
    $SUDO chmod a+r /etc/apt/keyrings/docker.asc

    $SUDO tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/$ID
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

    $SUDO apt-get update
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y \
        docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    if [[ -d /run/systemd/system ]]; then
        $SUDO systemctl enable --now docker
    else
        error "systemd is not running, so Docker can't start automatically. On WSL, enable systemd in /etc/wsl.conf."
    fi
}

if command -v docker >/dev/null 2>&1; then
    info "Docker is already installed: $(docker --version)"
else
    install_docker
fi

if ! docker compose version >/dev/null 2>&1; then
    error "Docker is installed but 'docker compose' is missing. Install the docker-compose-plugin package."
fi

# --- Let the user run Docker without sudo ---
TARGET_USER="${SUDO_USER:-$(id -un)}"

if [[ "$TARGET_USER" != "root" ]] \
    && getent group docker >/dev/null \
    && ! id -nG "$TARGET_USER" | grep -qw docker; then
    $SUDO usermod -aG docker "$TARGET_USER"
    info "Added $TARGET_USER to the docker group (takes effect after logging out and back in)."
fi