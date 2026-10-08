# Deckhand

Pick self-hosted apps from a terminal menu and get clean, portable Docker Compose setups. Installs Docker for you.

## Features

- **One-command setup.** Installs Docker from Docker's official repository, Python, and Deckhand itself.
- **A polished terminal menu.** Search, browse by category, and see each app's details before installing.
- **Plain Compose files you own.** Every app gets its own folder with a normal `docker-compose.yml`. Remove Deckhand and your apps keep working.
- **Generated secrets.** Database passwords are created randomly and stored in a `.env` file only you can read.
- **Safety checks.** Deckhand skips apps whose ports are already taken, never overwrites an existing setup, and tells you when an app is actually ready to use.

## Supported systems

- Ubuntu and Debian, including Raspberry Pi OS (64-bit)
- amd64 and arm64
- Ubuntu on WSL2, with systemd enabled

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/padou-dev/deckhand/main/install.sh | bash
```

> [!TIP]
> Prefer to read a script before running it? Download it first:
> ```bash
> curl -fsSL https://raw.githubusercontent.com/padou-dev/deckhand/main/install.sh -o install.sh
> less install.sh
> bash install.sh
> ```

Run the installer as your normal user, **not** with `sudo`. It asks for your password when it needs admin rights.

When it finishes, **log out and back in**, then run:

```bash
deckhand
```

## Using Deckhand

| Key | Action |
|---|---|
| `↑` `↓` | Move through a list |
| `Space` | Select or deselect an app |
| `Tab` | Switch between search, categories and apps |
| `/` | Jump to search |
| `Esc` | Back to the app list |
| `r` | Review your selection |
| `i` | Install the selected apps |
| `q` | Quit |
| `Ctrl+P` | Command palette (change theme and more) |

## Where things live

| Path | Contents |
|---|---|
| `~/deckhand_stacks/<app>/` | Each installed app: `docker-compose.yml`, `.env` and its data |
| `~/.local/share/deckhand/` | Deckhand itself |
| `~/.local/bin/deckhand` | The `deckhand` command |

## Managing apps after install

Every app is a standard Docker Compose project, so the usual commands work:

```bash
cd ~/deckhand_stacks/jellyfin
docker compose ps                              # status
docker compose logs -f                         # follow the logs
docker compose pull && docker compose up -d    # update to the latest image
docker compose down                            # stop and remove (data is kept)
```

## App catalog

| App | Category | Web address |
|---|---|---|
| Dozzle | Monitoring | http://localhost:8080 |
| Homepage | Management | http://localhost:3000 |
| Jellyfin | Media | http://localhost:8096 |
| Navidrome | Media | http://localhost:4533 |
| Nextcloud | Productivity | http://localhost:8085 |
| Nginx Proxy Manager | Network | http://localhost:81 (also uses ports 80 and 443) |
| Portainer | Management | https://localhost:9443 |
| Stirling-PDF | Productivity | http://localhost:8090 |
| Syncthing | Productivity | http://localhost:8384 |
| Uptime Kuma | Monitoring | http://localhost:3001 |
| Vaultwarden | Security | http://localhost:8222 |

From another device on your network, replace `localhost` with your server's IP address.

## Security notes

> [!WARNING]
> The installer adds your user to the `docker` group so you can run Docker without `sudo`. Membership in that group is equivalent to root access, because anyone who can start containers can mount the whole filesystem. This is the standard setup for a personal server, but don't give untrusted users access to that account.

- Each app's `.env` file holds its generated passwords and is readable only by your user.
- Vaultwarden's web vault requires HTTPS when used from other devices. Put it behind a reverse proxy such as Nginx Proxy Manager.

## Uninstall

```bash
rm -rf ~/.local/share/deckhand ~/.local/bin/deckhand
```

> [!NOTE]
> This removes Deckhand only. Your apps in `~/deckhand_stacks` keep running. To remove an app, run `docker compose down` in its folder, then delete the folder. Data folders created by containers may be owned by root, so you may need `sudo rm -r`.

## Adding an app

Each app is one YAML file in `catalog/`. The top half describes the app for Deckhand's menu; the bottom half is plain Docker Compose.

```yaml
id: uptime_kuma
name: Uptime Kuma
category: monitoring
description: Self-hosted uptime monitoring with a clean status dashboard.
architectures: [amd64, arm64]
web_port: 3001

services:
  uptime_kuma:
    image: louislam/uptime-kuma:2
    container_name: uptime_kuma
    ports:
      - "3001:3001"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Optional fields:
- `web_scheme: https` for apps that only serve HTTPS.
- `env:` for values written to the app's `.env` file. Use `${NAME}` in the compose section to reference them. Special values:
  - `generate`: a random password
  - `timezone`: the system's timezone
  - `host_ip`: the server's LAN IP address
  - anything else is used as written

## Troubleshooting

- **`permission denied ... docker.sock`:** the docker group change hasn't applied yet. Log out and back in. On WSL, run `wsl --terminate <distro>` from PowerShell and reopen it.
- **`deckhand: command not found`:** `~/.local/bin` isn't on your `PATH` yet. Log out and back in.
- **An app was skipped because a port is in use:** something else is using that port. Run `ss -tlnp` to see what.
- **An app says it's running but the page won't load:** some apps take a minute on first start. Check with `docker compose logs -f` in the app's folder.
- **"systemd is not running" on WSL:** add `[boot]` and `systemd=true` to `/etc/wsl.conf`, then restart the distro.

## License

[MIT](LICENSE)