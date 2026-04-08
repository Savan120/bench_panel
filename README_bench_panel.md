# Frappe Bench Control Panel (`bench_panel.py`)

This guide shows everything needed to run `bench_panel.py` step by step, including required Python libraries and commands.

## 1. What This Script Does

`bench_panel.py` starts a Flask web panel to manage a Frappe bench:

- Start/stop bench
- Run/stop specific sites on custom ports
- Switch bench path
- Local and SSH-based bench/site control
- Live terminal logs inside the panel

## 2. Requirements

- OS: Linux (recommended)
- Python: `3.9+` (works well with `3.10+`)
- A valid Frappe bench folder (must contain `sites/`)
- `bench` CLI available in your bench (`env/bin/bench` or `bin/bench`)

## 3. Required Python Library

Only one external Python package is required:

- `Flask`

Install command:

```bash
python3 -m pip install Flask
```

## 4. Optional System Dependency (for SSH password login)

If you want remote SSH connection using password (not SSH key), install:

- `sshpass` (optional)

Install on Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y sshpass
```

## 5. Recommended Setup (Virtual Environment)

From your bench directory:

```bash
cd /home/solufy/frappe-bench
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install Flask
```

## 6. Environment Variables (Optional but Recommended)

You can set these before running:

```bash
export BENCH_PANEL_SECRET_KEY="change-this-to-a-strong-secret"
export BENCH_PANEL_PASSWORD="your-strong-panel-password"
export BENCH_SITE_PROTOCOL="http"
```

Defaults if not set:

- `BENCH_PANEL_SECRET_KEY=change-this-secret-key`
- `BENCH_PANEL_PASSWORD=admin123`
- `BENCH_SITE_PROTOCOL=http`

## 7. Run the Panel

Basic command:

```bash
python3 bench_panel.py --bench /absolute/path/to/your/frappe-bench
```

Example:

```bash
python3 bench_panel.py --bench /home/solufy/frappe-bench
```

Custom host/port:

```bash
python3 bench_panel.py --bench /home/solufy/frappe-bench --host 0.0.0.0 --port 5055
```

Debug mode:

```bash
python3 bench_panel.py --bench /home/solufy/frappe-bench --debug
```

## 8. Open in Browser

If started with default host/port:

- URL: `http://127.0.0.1:5055`
- Login password: value of `BENCH_PANEL_PASSWORD` (default: `admin123`)

## 9. Common Run Commands (Quick Reference)

Activate venv:

```bash
source /home/solufy/frappe-bench/.venv/bin/activate
```

Run panel:

```bash
python3 /home/solufy/frappe-bench/bench_panel.py --bench /home/solufy/frappe-bench
```

Stop panel (in terminal):

```bash
Ctrl + C
```

## 10. Troubleshooting

### Error: `No module named flask`

Install Flask:

```bash
python3 -m pip install Flask
```

### Error: `Bench path does not exist` or `Missing sites directory`

Use a correct bench path:

```bash
python3 bench_panel.py --bench /correct/absolute/bench/path
```

### SSH password-based features fail

Install `sshpass`:

```bash
sudo apt install -y sshpass
```

Or use SSH key-based login.

## 11. Security Notes

- Change default panel password (`BENCH_PANEL_PASSWORD`) before exposing the panel on network.
- Use a strong `BENCH_PANEL_SECRET_KEY`.
- If using `--host 0.0.0.0`, protect access using firewall/reverse proxy.

