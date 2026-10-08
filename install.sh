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