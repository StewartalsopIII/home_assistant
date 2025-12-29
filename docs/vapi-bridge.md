# Vapi UDP Bridge (ESPHome → Pi → Vapi → ESPHome)

This repo includes:

- `vapi_bridge/` — Python bridge service (runs on the Pi)
- `esphome/respeaker.yaml` — ESPHome config modified to stream audio over UDP after wake word detection

## 1) Secrets / Config

### Pi bridge `.env`

Copy `.env.example` to `.env` and fill in:

- `VAPI_PRIVATE_API_KEY` (Private API Key from `dashboard.vapi.ai`)
- `VAPI_ASSISTANT_ID`

Optional tuning:

- `VAPI_BRIDGE_UDP_PORT` (default `9123`)
- `VAPI_BRIDGE_IDLE_TIMEOUT_S` (ends the call after inactivity)
- `VAPI_BRIDGE_VOICE_RMS_THRESHOLD` (voice activity threshold)

### ESPHome `secrets.yaml`

Add the bridge IP to `esphome/secrets.yaml`:

```yaml
vapi_bridge_ip: "192.168.2.65"
```

## 2) Install Python deps (Pi)

From the repo root:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r vapi_bridge/requirements.txt
```

## 3) Run the bridge (manual)

```bash
. .venv/bin/activate
python -m vapi_bridge.main
```

By default, the bridge will read `./.env` automatically (it won’t override already-exported environment variables).

## 4) Run the bridge as a service (systemd)

Copy the unit file and enable it:

```bash
sudo cp vapi-bridge.service /etc/systemd/system/vapi-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now vapi-bridge.service
sudo systemctl status vapi-bridge.service
```

If you use a venv, edit `/etc/systemd/system/vapi-bridge.service` to point `ExecStart` at:

`/home/stewartalsop/prototypes/home-assistant/.venv/bin/python -m vapi_bridge.main`

## 5) Flash ESPHome

Use the ESPHome dashboard (http://192.168.2.65:6052) to compile + upload `esphome/respeaker.yaml`.

## Notes

- This bypasses Home Assistant’s Assist pipeline entirely: wake word → UDP mic stream → Vapi → UDP speaker stream.
- UDP packets are deliberately kept under ~508 bytes because ESPHome’s `udp` component receive buffer is sized that way.
