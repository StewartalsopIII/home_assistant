# ReSpeaker XVF3800 Integration - Current Status

**Date:** 2025-12-12 08:30
**Status:** Device offline after firmware re-flash - not responding to network

## Problem Statement

After re-flashing the ESPHome firmware to fix an encryption key mismatch, the ReSpeaker device is no longer responding on the network. The device does not respond to ping, mDNS lookup returns no results, and USB serial produces no output. The device may be stuck in a boot loop or failing to connect to WiFi.

---

## Session Synopsis (2025-12-12)

### What We Did Today

1. **Verified initial state:** Device was online at 192.168.2.13, API port 6053 open, but Home Assistant couldn't connect
2. **Identified root cause:** Home Assistant logs showed "Connection requires encryption" followed by "Invalid encryption key" - the device had encryption enabled but HA was using wrong/no key
3. **Added device to Home Assistant:** User went through Settings → Devices & Services → ESPHome → Add with IP 192.168.2.13 and encryption key
4. **Hit voice assistant wizard:** HA prompted to set up voice assistant - tried "Full local processing" but Docker installations don't support add-ons
5. **Skipped wizard:** User wants to use VAPI (external voice AI) instead of HA's built-in voice processing, so we skipped the wizard
6. **Encryption key mismatch:** HA logs showed "Invalid encryption key" - the key in HA config didn't match what was on the device firmware
7. **Re-flashed firmware:** Uploaded firmware via USB to ensure device has correct encryption key (`<API_ENCRYPTION_KEY>`)
8. **Device went offline:** After firmware flash, device stopped responding to ping
9. **Power cycled:** Unplugged and replugged USB - still no response
10. **Enabled integration:** User had disabled the ESPHome integration entry, re-enabled it
11. **Still offline:** Device not responding to ping, no serial output, no mDNS resolution

### Current Problem

**The device is completely unresponsive after firmware re-flash:**
- No response to `ping 192.168.2.13`
- No mDNS resolution for `respeaker-xvf3800-assistant.local`
- No output from USB serial (`/dev/ttyACM0`)
- Home Assistant shows "Error connecting... [Errno 113] Connect call failed"

### Intended Solution

1. **Check if device is booting:** Look for LED activity on the ReSpeaker board
2. **Try different USB port/cable:** Rule out USB power issues
3. **Wait longer:** ESP32 boot + WiFi connection can take 30-60 seconds
4. **Check serial with proper tool:** Use `minicom` or `screen` to view boot logs
5. **If still stuck:** May need to erase flash and re-upload firmware completely
6. **Verify WiFi credentials:** Ensure `secrets.yaml` has correct SSID/password

---

## Original Status (2025-12-11)

### Previous Problem Statement

The ReSpeaker XVF3800 + ESP32-S3 device has been successfully flashed with ESPHome firmware that includes the required API encryption key. The device is online and functioning at the hardware level, but Home Assistant cannot establish a stable API connection to the device, resulting in all entities showing as "Unavailable."

## Current State

### ✅ Working Components
- **Hardware:** ReSpeaker XVF3800 + ESP32-S3 board functioning
- **XMOS Firmware:** v1.0.5 audio processing chip operational
- **ESPHome Firmware:** Successfully compiled and uploaded (2025.11.5)
- **WiFi Connection:** Device connected to `<WIFI_SSID>` network
- **Network Address:** 192.168.2.13 (changed from previous 192.168.2.12)
- **mDNS Resolution:** respeaker-xvf3800-assistant.local resolving correctly
- **USB Serial:** Connected at /dev/ttyACM0, logs accessible

### ❌ Failing Component
- **Home Assistant API Connection:** Socket operation errors (BAD_INDICATOR errno=11)
- **Symptom:** Home Assistant shows "Unable to connect to the ESPHome device"
- **Effect:** All device entities (microphone, speaker, wake word, etc.) show "Unavailable"

## Technical Details

### Device Information
```
Hostname:    respeaker-xvf3800-assistant
IP Address:  192.168.2.13
MAC Address: 9C:13:9E:AD:0F:50
Firmware:    ESPHome 2025.11.5
XMOS:        v1.0.5
Chip:        ESP32-S3 (QFN56) revision v0.2
Features:    Wi-Fi, BT 5, Dual Core, 8MB Flash, 8MB PSRAM
USB:         /dev/ttyACM0 (USB-Serial/JTAG)
```

### Network Configuration
```
Raspberry Pi:    192.168.2.65
ReSpeaker:       192.168.2.13
WiFi Network:    <WIFI_SSID>
Connection:      ESPHome Native API (encrypted, port 6053)
```

### Encryption Key
```yaml
api_encryption_key: "<API_ENCRYPTION_KEY>"
```
**Location:** `/home/stewartalsop/prototypes/home-assistant/esphome/secrets.yaml`

## Error Messages from Logs

```
[21:06:37.895][W][api.connection:1889]: 192.168.2.65 (192.168.2.65): Socket operation failed BAD_INDICATOR errno=11
[21:09:27.480][W][api.connection:205]: 192.168.2.65 (192.168.2.65) is unresponsive; disconnecting
```

**errno=11** typically means "Resource temporarily unavailable" (EAGAIN) - suggests socket timing or buffer issues.

## What Was Done Today

1. ✅ Identified root cause: Missing API encryption key in ESPHome config
2. ✅ Generated base64-encoded 32-byte encryption key
3. ✅ Added encryption key to `secrets.yaml` and `respeaker.yaml`
4. ✅ Removed incompatible "stop" wake word model from config
5. ✅ Successfully compiled firmware (11 minutes, 2.97MB)
6. ✅ Uploaded firmware via USB after OTA failed
7. ✅ Device booted and connected to WiFi at new IP (192.168.2.13)
8. ✅ XMOS audio chip initialized successfully
9. ❌ Home Assistant API connection failing with socket errors

## Attempted Solutions

### Home Assistant Side
1. **Tried entering encryption key manually:** Got "Unable to connect" error
2. **Device was previously auto-discovered:** Old connection without encryption cached

### Not Yet Attempted
- Remove and re-add device in Home Assistant ESPHome integration
- Check Home Assistant firewall/network settings
- Verify ESPHome API port (6053) is accessible
- Check Home Assistant logs for more detailed error messages
- Restart Home Assistant Docker container

## Next Steps to Try

### Option 1: Fresh Integration (Recommended)
1. Remove old device from Home Assistant ESPHome integration
   - Settings → Devices & Services → ESPHome
   - Find ReSpeaker device → 3 dots → Delete
2. Add device fresh with new IP and encryption key
   - Click "+ ADD INTEGRATION" → Search "ESPHome"
   - Host: `192.168.2.13`
   - Encryption key: `<API_ENCRYPTION_KEY>`

### Option 2: Restart Home Assistant
```bash
cd /home/stewartalsop/prototypes/home-assistant
docker compose restart homeassistant
# Wait 30 seconds, then check if device auto-connects
```

### Option 3: Check Network Connectivity
```bash
# Test if HA can reach device
docker exec homeassistant ping -c 3 192.168.2.13

# Check if API port is open
nc -zv 192.168.2.13 6053

# Check Home Assistant logs
docker logs homeassistant -f | grep -i respeaker
```

### Option 4: Verify ESPHome Config
```bash
# Validate config
cd /home/stewartalsop/prototypes/home-assistant/esphome
docker run --rm -v "${PWD}":/config ghcr.io/esphome/esphome config respeaker.yaml

# Check if API section is properly configured
grep -A 10 "^api:" respeaker.yaml
```

## Configuration Files

### Primary Config
**Path:** `/home/stewartalsop/prototypes/home-assistant/esphome/respeaker.yaml`
- Lines 117-162: API configuration with encryption key
- Line 120: `key: !secret api_encryption_key`

### Secrets File
**Path:** `/home/stewartalsop/prototypes/home-assistant/esphome/secrets.yaml`
```yaml
wifi_ssid: "<WIFI_SSID>"
wifi_password: "<WIFI_PASSWORD>"
ota_password: "<OTA_PASSWORD>"
api_encryption_key: "<API_ENCRYPTION_KEY>"
```

### Docker Compose
**Path:** `/home/stewartalsop/prototypes/home-assistant/docker-compose.yml`
- Home Assistant: port 8123, network_mode: host
- ESPHome Dashboard: port 6052, network_mode: host

## Access URLs

- **Home Assistant:** http://192.168.2.65:8123
- **ESPHome Dashboard:** http://192.168.2.65:6052
- **Device (direct):** http://192.168.2.13 (if web server enabled)

## Diagnostic Commands

```bash
# Check device is online
ping 192.168.2.13

# View live device logs
cd /home/stewartalsop/prototypes/home-assistant/esphome
docker run --rm --device=/dev/ttyACM0 -v "${PWD}":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0

# Or via network (if API working)
docker run --rm -v "${PWD}":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device 192.168.2.13

# Check Home Assistant can see device
docker exec homeassistant ping -c 3 192.168.2.13

# View Home Assistant logs
docker logs homeassistant -f | grep -i esphome

# Restart Home Assistant
cd /home/stewartalsop/prototypes/home-assistant
docker compose restart homeassistant
```

## Known Issues

1. **IP Address Changed:** Device was at 192.168.2.12, now at 192.168.2.13
   - Old cached connection in Home Assistant may be causing issues
   - mDNS resolution working, so hostname should work

2. **Socket Errors:** errno=11 (EAGAIN) suggests timing/buffer issues
   - May be network latency between containers
   - Could be Home Assistant's ESPHome component having stale connection

3. **Stop Wake Word Model Removed:**
   - URL was invalid/incompatible
   - Feature is optional, doesn't affect basic functionality

## Expected Behavior Once Fixed

After successful Home Assistant connection:

1. **Device Page:** All entities show current values (not "Unavailable")
2. **Entities Available:**
   - `media_player.respeaker_xvf3800_assistant` - Speaker/audio playback
   - `binary_sensor.respeaker_microphone_mute` - Microphone mute status
   - `sensor.respeaker_firmware_version` - Shows "2025.9.0"
   - `select.respeaker_wake_word` - Wake word selection (Okay Nabu, etc.)
   - `select.respeaker_wake_word_sensitivity` - Sensitivity adjustment
   - `number.respeaker_led_ring_brightness` - LED brightness control
   - `select.respeaker_led_ring_color_preset` - LED color selection
   - Voice assistant integration entities

3. **Voice Assistant:** Ready to configure pipeline and test wake word

## References

- **Setup Guide:** `~/prototypes/home-assistant/docs/setup-2025-12-11.md`
- **Troubleshooting:** `~/prototypes/home-assistant/docs/troubleshooting-2025-12-11.md`
- **FormatBCE Integration:** https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration
- **ESPHome Docs:** https://esphome.io/components/api.html

## Summary for Quick Context

**The Goal:** Integrate ReSpeaker XVF3800 voice hardware with Home Assistant for voice assistant functionality.

**Current Blocker:** Device is flashed and online with correct firmware and encryption key, but Home Assistant cannot establish stable API connection (socket errors). Need to either remove/re-add device in Home Assistant or investigate network/configuration issues preventing the encrypted API handshake.

**Quick Win:** Most likely solution is to delete the old ESPHome device entry in Home Assistant and add it fresh with the new IP (192.168.2.13) and encryption key.
