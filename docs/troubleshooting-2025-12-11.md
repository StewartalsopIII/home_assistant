# ReSpeaker XVF3800 Integration Troubleshooting

**Date:** 2025-12-11
**Status:** Firmware compiled successfully, upload in progress

## Current Issue

The ReSpeaker XVF3800 + ESP32-S3 device successfully flashed with ESPHome firmware but shows as "Unavailable" in Home Assistant. Attempting to reflash with updated configuration that includes API encryption key.

### Problem Summary

1. **Device Discovery:** Device auto-discovered in Home Assistant but all entities show "Unavailable"
2. **Root Cause:** ESPHome firmware missing API encryption key for secure communication with Home Assistant
3. **Current State:** New firmware compiled with encryption key, attempting to upload via USB after OTA upload failed

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│ Raspberry Pi 5 (192.168.2.65)                       │
│                                                      │
│  ┌────────────────┐        ┌──────────────────┐    │
│  │ Home Assistant │◄──────►│ ESPHome Dashboard│    │
│  │ (Docker:8123)  │        │ (Docker:6052)    │    │
│  └────────────────┘        └──────────────────┘    │
│         │                          │                │
│         │ ESPHome API              │ Compile/Flash  │
│         │ (Encrypted)              │                │
└─────────┼──────────────────────────┼────────────────┘
          │                          │
          │                          ▼
          │                  ┌─────────────────┐
          │                  │ USB Connection  │
          │                  │ (/dev/ttyACM0)  │
          │                  └─────────────────┘
          │                          │
          ▼                          ▼
    ┌──────────────────────────────────────┐
    │ ReSpeaker XVF3800 + ESP32-S3         │
    │                                       │
    │ - Current IP: 192.168.2.12 (offline) │
    │ - Hostname: respeaker-xvf3800-       │
    │   assistant.local                    │
    │ - MAC: 9C:13:9E:AD:0F:50             │
    │ - Firmware: ESPHome 2025.11.5        │
    │ - XMOS Audio: v1.0.5                 │
    └──────────────────────────────────────┘
```

## Key Components

### Hardware
- **ReSpeaker XVF3800:** Far-field voice capture board with 4-mic array
- **ESP32-S3:** Microcontroller with WiFi/Bluetooth, 8MB flash, 8MB PSRAM
- **XMOS XVF3800:** Dedicated audio DSP chip for beamforming and echo cancellation
- **Raspberry Pi 5:** Host running Docker containers for Home Assistant and ESPHome

### Software Stack
- **ESPHome:** Firmware framework that runs on ESP32-S3, bridges device to Home Assistant
- **Home Assistant:** Open-source home automation platform (Docker container)
- **ESPHome Dashboard:** Web interface for managing ESPHome devices (Docker container)
- **XMOS Firmware:** v1.0.5 - low-level firmware for audio processing chip

### Network Configuration
- **WiFi Network:** <WIFI_SSID>
- **Raspberry Pi:** 192.168.2.65
- **ReSpeaker (Expected):** 192.168.2.12
- **Communication Protocol:** ESPHome Native API over TCP with encryption

## Critical Configuration Files

### Primary Config
**Location:** `/home/stewartalsop/prototypes/home-assistant/esphome/respeaker.yaml`
- ESPHome device configuration (1757 lines)
- Defines hardware pins, wake words, voice assistant integration
- Recently modified to add API encryption key

### Secrets
**Location:** `/home/stewartalsop/prototypes/home-assistant/esphome/secrets.yaml`
```yaml
wifi_ssid: "<WIFI_SSID>"
wifi_password: "<WIFI_PASSWORD>"
ota_password: "<OTA_PASSWORD>"
api_encryption_key: "<API_ENCRYPTION_KEY>"  # Added today
```

### Docker Compose
**Location:** `/home/stewartalsop/prototypes/home-assistant/docker-compose.yml`
- Runs Home Assistant on port 8123
- Runs ESPHome on port 6052
- Both use `network_mode: host` for mDNS/discovery

## Upload Methods

### OTA (Over-The-Air)
- **Preferred Method:** Upload via WiFi network
- **Requirement:** Device must be online at 192.168.2.12
- **Port:** TCP 3232
- **Current Status:** Failed - device unreachable on network

### USB Serial
- **Fallback Method:** Upload via USB connection
- **Device:** `/dev/ttyACM0`
- **Chip:** ESP32-S3 USB-Serial/JTAG
- **Current Status:** Upload experiencing serial communication errors

## Troubleshooting Steps

### 1. Check Device Network Connectivity
```bash
# Ping test
ping -c 3 192.168.2.12

# mDNS resolution
ping -c 3 respeaker-xvf3800-assistant.local

# Check Home Assistant logs
docker logs homeassistant -f | grep -i respeaker

# Check ESPHome dashboard
# Visit: http://192.168.2.65:6052
```

### 2. Verify USB Connection
```bash
# Check if device is connected
ls -la /dev/ttyACM0

# Monitor serial output
screen /dev/ttyACM0 115200

# Or use ESPHome logs
cd /home/stewartalsop/prototypes/home-assistant
docker run --rm --device=/dev/ttyACM0 -v "${PWD}":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0
```

### 3. Power Cycle Recovery
```bash
# Physical power cycle
# 1. Unplug USB cable from ReSpeaker
# 2. Wait 10 seconds
# 3. Replug USB cable
# 4. Wait 30-60 seconds for WiFi connection
# 5. Verify with: ping 192.168.2.12
```

### 4. Compile and Upload (OTA)
```bash
cd /home/stewartalsop/prototypes/home-assistant/esphome

# Compile and upload over WiFi
docker run --rm -v "${PWD}":/config ghcr.io/esphome/esphome \
  run respeaker.yaml --device 192.168.2.12
```

### 5. Compile and Upload (USB)
```bash
cd /home/stewartalsop/prototypes/home-assistant/esphome

# Compile and upload via USB
docker run --rm --device=/dev/ttyACM0 -v "${PWD}":/config \
  ghcr.io/esphome/esphome run respeaker.yaml --device /dev/ttyACM0
```

## Expected Behavior After Fix

Once the new firmware with encryption key is successfully uploaded:

1. **Device boots** and connects to WiFi (192.168.2.12)
2. **mDNS advertises** `respeaker-xvf3800-assistant.local`
3. **Home Assistant connection** established using encrypted API
4. **All entities become available:**
   - Microphone entity
   - Speaker/media player
   - Assist satellite (voice assistant)
   - LED controls
   - Wake word configuration
   - Sensors (alarm time, firmware version, etc.)

## Integration with Home Assistant

After device is online and connected:

1. **Navigate to:** Settings → Devices & Services
2. **ESPHome Integration** should show connected device
3. **Configure:**
   - Assistant: Preferred voice assistant pipeline
   - Wake Word: Default is "Okay Nabu"
   - Sensitivity: Adjustable via dropdown
   - LED effects: Color and brightness

## Important Notes

### Encryption Key Requirement
- **ESPHome API requires encryption** for security
- Key must be **base64-encoded, 32 bytes**
- Key in config must match key Home Assistant uses to connect
- **Current key:** `<API_ENCRYPTION_KEY>`

### Home Assistant Auto-Discovery
- Device was auto-discovered **before** encryption key was added
- Home Assistant may have cached old connection parameters
- After reflash, may need to:
  1. Remove device from ESPHome integration in Home Assistant
  2. Re-add device with new encryption key
  3. Or: Home Assistant will auto-prompt for encryption key

### Firmware Build Location
Compiled firmware is stored at:
```
/home/stewartalsop/prototypes/home-assistant/esphome/.esphome/build/
respeaker-xvf3800-assistant/.pioenvs/respeaker-xvf3800-assistant/
├── firmware.bin          # Main application
├── firmware.ota.bin      # OTA update format
├── firmware.factory.bin  # Full flash image
├── bootloader.bin        # ESP32 bootloader
└── partitions.bin        # Partition table
```

## Wake Word Models

Device supports multiple wake words (configured in YAML):
- **okay_nabu** (primary)
- **kenobi**
- **hey_jarvis**
- **hey_mycroft**

Note: "stop" wake word model was removed due to incompatibility issues.

## Next Steps After Successful Upload

1. Verify device appears online in ESPHome Dashboard
2. Check device shows "ONLINE" status
3. Verify WiFi connection and IP assignment
4. Test Home Assistant connection
5. Configure voice assistant pipeline in Home Assistant
6. Test wake word detection and voice commands

## Resources

- **ESPHome Config:** `~/prototypes/home-assistant/esphome/respeaker.yaml`
- **Setup Documentation:** `~/prototypes/home-assistant/docs/setup-2025-12-11.md`
- **Home Assistant URL:** http://192.168.2.65:8123
- **ESPHome Dashboard URL:** http://192.168.2.65:6052
- **FormatBCE Integration:** https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration
