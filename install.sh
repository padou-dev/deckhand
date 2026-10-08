#!/usr/bin/env bash
#
# Stowage installer: installs Docker and Python, then launches Stowage.

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
        error "Unsupported distribution: $ID. Stowage currently supports Ubuntu and Debian."
        ;;
esac

# --- Don't run the whole script with sudo ---
if [[ "$EUID" -eq 0 && -n "${SUDO_USER:-}" ]]; then
    error "Please run this script without sudo. It will ask for your password when needed."
fi

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

# --- Install Python and git ---
info "Installing Python and git..."
$SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv git

# --- Get Stowage's files ---
INSTALL_DIR="$HOME/.local/share/stowage"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-.}")" && pwd)"

if [[ -f "$SCRIPT_DIR/stowage/app.py" ]]; then
    info "Installing from local copy: $SCRIPT_DIR"
    mkdir -p "$INSTALL_DIR"
    rm -rf "$INSTALL_DIR/stowage" "$INSTALL_DIR/catalog"
    cp -r "$SCRIPT_DIR/stowage" "$SCRIPT_DIR/catalog" "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
elif [[ -d "$INSTALL_DIR/.git" ]]; then
    info "Updating Stowage..."
    git -C "$INSTALL_DIR" pull --ff-only
else
    info "Downloading Stowage..."
    git clone https://github.com/padou-dev/stowage.git "$INSTALL_DIR"
fi

# --- Set up Stowage's Python environment ---
info "Setting up Python environment..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# --- Create the 'stowage' command ---
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/stowage" <<EOF
#!/usr/bin/env bash
cd "$INSTALL_DIR"
exec "$INSTALL_DIR/.venv/bin/python" -m stowage.app "\$@"
EOF
chmod +x "$HOME/.local/bin/stowage"

info "Stowage is installed!"
info "Log out and back in (so the docker group and PATH changes apply), then run: stowage"