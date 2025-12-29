# Errors encountered (2025-12-29)

This is a running log of the notable failures we hit while wiring up a ReSpeaker XVF3800 (XIAO ESP32-S3) + ESPHome + Raspberry Pi bridge to Vapi, with the chosen architecture of **ESPHome → UDP → Pi bridge → Vapi WebSocket** (bypassing HA Assist voice).

It’s written so future-me can quickly recognize a symptom, understand the likely cause, and apply the right fix without re-learning everything.

## 1) GitHub push/authentication errors (HTTPS)

### Symptom
- `remote: Invalid username or token. Password authentication is not supported for Git operations.`
- `remote: Permission ... denied ... (403)`

### Cause
- GitHub no longer supports password authentication over HTTPS for Git operations.
- A GitHub Personal Access Token (PAT) is required; the PAT must have permissions to write to the repo.

### Fix
- Use **HTTPS + PAT**: when Git prompts for a “password”, paste the token.
- Ensure the token has repo write permissions (fine-grained PAT: allow the specific repo + "Contents: Read and write").

### Notes
- After the PAT was used correctly, `git push -u origin main` succeeded.
- Avoid committing secrets: keep `.env`, `secrets.yaml`, tokens, keys in `.gitignore`.

## 2) Vapi key confusion (public vs private)

### Symptom
- Uncertainty whether `VAPI_API_KEY` should be a “public key” or something else.

### Cause
- Vapi distinguishes:
  - **Private API keys**: server-side access (what the Pi bridge must use).
  - **Public API keys**: client SDK access (browser/mobile), not appropriate for the Pi bridge.

### Fix
- Bridge uses `VAPI_PRIVATE_API_KEY` (server-side) + `VAPI_ASSISTANT_ID`.

## 3) ESPHome “Install” UI confusion (Compile/Flash vs Install/Validate)

### Symptom
- In ESPHome Dashboard, no explicit “Compile/Flash” button; only “Install” and “Validate”.

### Cause
- In ESPHome UI, **Install** performs compile + upload (OTA or serial) depending on selection.

### Fix
- Use **Install** to build and upload.

## 4) OTA upload failures: mDNS / host not found

### Symptom
- `ERROR Error resolving IP address of ['respeaker-xvf3800-assistant.local']. Is it connected to WiFi?`
- `Timeout resolving IP address ...`
- `WARNING Failed to upload to ['respeaker-xvf3800-assistant.local']`

### Likely causes
- Device is not on Wi‑Fi (powered down, wrong Wi‑Fi creds, stuck in provisioning firmware).
- mDNS `.local` name resolution not working on the LAN.
- Device IP changed (DHCP lease changed), so the old IP is wrong.

### Fixes
- Confirm device is online:
  - `ping <device-ip>` (host unreachable means it’s not at that IP)
- Prefer using the device’s actual IP (once known) rather than mDNS.
- If it’s offline: flash via USB serial (or recover Wi‑Fi provisioning).

## 5) Device appeared “lost” / changed behavior after ESPHome Web onboarding

### Symptom
- Home Assistant shows the ReSpeaker entities as `unavailable`.
- The device stops responding on the prior LAN IP.
- Logs show **AP mode** with SSID like `esphome-web-...` and IP `192.168.4.1`.

### Cause
- The device was running ESPHome Web’s **temporary provisioning firmware** (Project `esphome.web`), not the intended ReSpeaker firmware.
- This can happen if “Prepare for first use” is used instead of flashing the actual compiled `.bin`.

### Fix
- Flash the correct compiled firmware using ESPHome Web:
  - Select the **factory** `.bin` (example: `respeaker-xvf3800-assistant.factory.bin`)
  - Do not rely on “Prepare for first use” unless you specifically intend to use Improv Wi‑Fi provisioning.

## 6) “Improv Wi‑Fi serial not detected”

### Symptom
- ESPHome Web: `Improv Wi-Fi serial not detected`

### Cause
- Not all ESPHome firmwares/devices support Improv Serial onboarding.
- This is not required if Wi‑Fi credentials are already baked into the firmware.

### Fix
- Skip “Prepare for first use” and instead flash the actual firmware `.bin`.

## 7) WebSerial / ESPHome Web: “Failed to open serial port”

### Symptom
- `web.esphome.io says: Failed to execute 'open' on 'SerialPort': Failed to open serial port.`

### Common causes (seen here)
- The serial port was already open by another Chromium instance/tab.
  - `sudo fuser -v /dev/ttyACM0` showed `chromium` holding the device.

### Fix
- Close all tabs/windows using WebSerial or quit Chromium; then reconnect.
- Verify the port isn’t held:
  - `sudo fuser -v /dev/ttyACM0`

### Notes
- On the Pi, the ESP32-S3 typically appears as `/dev/ttyACM0` (“USB JTAG/Serial Debug Unit”).

## 8) Missing debug tools

### Symptom
- `tcpdump: command not found`
- `arp-scan: command not found`

### Cause
- Packages not installed on the Pi base system.

### Fix
- Install when needed (examples):
  - `sudo apt-get install tcpdump`
  - `sudo apt-get install arp-scan`

## 9) ESPHome API / connection noise

### Symptom
- `[W][api.connection:...]: 192.168.2.65 ... Socket operation failed BAD_INDICATOR errno=11`
- Occasional handshake timeouts.

### Notes
- This looked like intermittent ESPHome API/transport flakiness and wasn’t the primary blocker for Vapi.
- If it becomes frequent, investigate Wi‑Fi RSSI, AP isolation, router multicast behavior, and ESPHome API encryption settings.

## 10) Core streaming failure: UDP `sendto() error 12` (ESP32)

### Symptom
- `[W][udp:146][mic_task]: sendto() error 12` repeated rapidly, typically after wake word/session start.
- Pi bridge shows no received packets; Vapi never starts.

### Cause (most likely)
- On ESP32/lwIP, errno `12` is typically **out of memory / no buffers**.
- Triggered by attempting to send too much audio too fast over UDP:
  - capturing at **48kHz / 32‑bit / stereo** and sending many small UDP packets overwhelms lwIP buffers.

### ✅ RESOLVED (2025-12-29)

**Solution**: Changed microphone sample_rate from 48000 to 16000 in `esphome/respeaker.yaml` line 1217.

```yaml
microphone:
  - platform: i2s_audio
    sample_rate: 16000  # Changed from 48000
```

**Results**:
- Bandwidth reduced: 384 KB/sec → 128 KB/sec (3x reduction)
- UDP errors completely eliminated
- Voice assistant now works reliably
- Audio flows properly to Home Assistant Assist

**Why it worked**: The ESP32's hardware I2S interface supports 16kHz natively, eliminating the need for complex software downsampling. This simple one-line change proved the "DHH approach" - try the simplest thing first.

**Commit**: `b50f7d6` - "Fix: Reduce microphone sample rate to 16kHz to resolve UDP bandwidth issue"

### Fix direction (implemented)
- ✅ Reduced sample rate at hardware level (48kHz → 16kHz)
- ✅ Verified ESPHome YAML path matches container mount (`/config/respeaker.yaml`)
- ✅ Tested end-to-end: wake word → speech recognition → response

### Why this matters
- This was the **critical blocking issue** preventing voice assistant from working
- Without this fix, no audio could flow from ESP32 to any voice service

## 11) Repo path mismatch: `/config/respeaker.yaml` vs `esphome/respeaker.yaml`

### Symptom
- ESPHome build output references `/config/respeaker.yaml`, but edits were made in the repo under `esphome/respeaker.yaml`.

### Cause
- ESPHome running in Docker commonly uses a mounted `/config` directory. If the container is mounting a different folder/YAML than the one being edited, changes won’t reach the compiled firmware.

### Fix
- Confirm which file the ESPHome container uses for the device (the exact YAML it reads).
- Ensure edits are applied to that YAML before compiling/flashing.

## 12) Local tool sandbox failures (agent environment)

### Symptom
- Tool commands failed with: `error running landlock: Sandbox(LandlockRestrict)`

### Cause
- The execution environment sandbox (Landlock) failed to initialize for some tool invocations.

### Fix
- Commands were re-run with “escalated” tool execution to proceed.

