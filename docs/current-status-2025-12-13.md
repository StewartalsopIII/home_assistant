# ReSpeaker XVF3800 Integration - Comprehensive Status

**Date:** 2025-12-13 06:10
**Status:** Device online but encryption handshake failing - entities show "Unavailable"

---

## Executive Summary

**What's Working:**
- ✅ Device is online and responding to ping at 192.168.2.13
- ✅ USB device detected at /dev/ttyACM0
- ✅ Home Assistant recognizes the device
- ✅ WiFi connection stable to `<WIFI_SSID>`

**What's NOT Working:**
- ❌ **LED ring not blinking** (was blinking strongly for weeks before)
- ❌ Encryption handshake fails between Home Assistant and device
- ❌ All Home Assistant entities show "Unavailable"
- ❌ ESPHome API connection drops immediately after encrypted hello

**Root Cause:**
Encryption key mismatch between device firmware and Home Assistant configuration. The device may be running old firmware without the encryption key, or Home Assistant has cached old device information.

---

## Timeline of Events

### 2025-12-11 (Initial Setup)
1. ✅ Set up Home Assistant + ESPHome in Docker containers
2. ✅ Flashed ReSpeaker with ESPHome firmware (FormatBCE integration)
3. ✅ Device came online at 192.168.2.12
4. ❌ Home Assistant couldn't connect - missing encryption key
5. ✅ Generated encryption key: `<API_ENCRYPTION_KEY>`
6. ✅ Added key to secrets.yaml and respeaker.yaml
7. ✅ Compiled firmware (11 minutes, 2.97MB)
8. ⚠️  Attempted to upload via USB
9. ❌ Home Assistant API connection still failing with socket errors

### 2025-12-12 (Re-flash Attempt)
1. ⚠️  Device IP changed from 192.168.2.12 to 192.168.2.13
2. ⚠️  Attempted firmware re-flash via USB to add encryption key
3. ❓ **UNDOCUMENTED:** Did the flash complete successfully?
4. ❓ **UNDOCUMENTED:** What happened between Dec 12 and Dec 13?
5. ❌ Device reported as "offline" - no ping response (per docs)
6. ❌ No serial output from USB
7. ❌ No mDNS resolution

### 2025-12-13 (Current State - CONTRADICTS DEC 12 DOCS)
1. ✅ **Device IS responding to ping** at 192.168.2.13
2. ✅ USB device detected at /dev/ttyACM0
3. ❌ **NEW SYMPTOM:** LED ring not blinking at all
4. ❌ Home Assistant error: `"The connection dropped immediately after encrypted hello"`
5. ⚠️  Home Assistant storage shows compilation time: "Dec 11 2025, 20:49:10"
6. ❓ **CRITICAL GAP:** Why does HA show Dec 11 firmware if we re-flashed on Dec 12?

---

## Current Diagnostic Results (2025-12-13 06:05)

### Network Connectivity
```bash
# Ping test
ping -c 2 192.168.2.13
# RESULT: SUCCESS - 29.3ms / 14.7ms response time
# CONCLUSION: Device is online and responding
```

### USB Connection
```bash
ls -la /dev/ttyACM0
# RESULT: crw-rw----+ 1 root plugdev 166, 0 Dec 13 06:05 /dev/ttyACM0
# CONCLUSION: USB device detected and accessible
```

### Home Assistant Logs
```
2025-12-12 19:11:38 WARNING [aioesphomeapi.reconnect_logic]
Can't connect to ESPHome API for respeaker-xvf3800-assistant @ 192.168.2.13:
The connection dropped immediately after encrypted hello;
Try enabling encryption on the device or turning off encryption on the client
(EncryptionHelloAPIError)
```

**Translation:** Home Assistant IS trying to use encryption, and the device IS responding on port 6053, but the encryption handshake is failing. This means:
- The device is running firmware that responds to encrypted connections
- But the encryption key doesn't match
- Or the device firmware doesn't actually have encryption enabled

### Home Assistant Device Info
From `.storage/esphome.01KC92468VWAFR7R2G744W1QTZ`:
```json
{
  "name": "respeaker-xvf3800-assistant",
  "compilation_time": "Dec 11 2025, 20:49:10",
  "esphome_version": "2025.11.5",
  "project_version": "2025.9.0",
  "api_encryption_supported": true
}
```

**CRITICAL FINDING:** Compilation time shows Dec 11, NOT Dec 12. This suggests:
1. The Dec 12 firmware flash did NOT complete successfully, OR
2. The device is still running the Dec 11 firmware, OR
3. Home Assistant cached old device information and hasn't updated

### Port Tests
```bash
# Web server test
curl http://192.168.2.13
# RESULT: Connection refused on port 80
# CONCLUSION: Web server is not enabled in firmware (expected)

# API port test
# RESULT: nc command not available on Pi
# CONCLUSION: Cannot verify port 6053 directly
```

---

## Undocumented Issues & Open Questions

### 🔴 CRITICAL: LED Behavior Not Documented

**Current Symptom:**
- ReSpeaker LED ring shows NO activity (no blinking)
- Previously was "blinking strongly for weeks"
- Device plugged into USB to Raspberry Pi

**Missing Documentation:**
1. What SHOULD the LED ring do in different states?
   - During boot?
   - When connected to WiFi?
   - When connected to Home Assistant?
   - When idle/ready?
   - When listening for wake word?
   - When processing voice command?

2. What does "no LED activity" indicate?
   - Power issue?
   - Firmware not running?
   - Boot loop?
   - Low-level hardware problem?
   - LED control disabled in config?

3. How to diagnose LED issues?
   - Check LED brightness setting in HA?
   - Check LED control in ESPHome config?
   - Force LED test via API call?

**Action Needed:** Document expected LED behavior and troubleshooting guide.

### 🔴 CRITICAL: Encryption Handshake Failure

**Current Error:**
```
The connection dropped immediately after encrypted hello;
Try enabling encryption on the device or turning off encryption on the client
```

**What This Means:**
1. Home Assistant initiates connection to device on port 6053
2. Device responds (so it's listening)
3. Home Assistant sends encrypted "hello" message
4. Device receives it but immediately drops the connection

**Possible Causes:**
1. Device firmware doesn't have encryption enabled (config has it, but firmware doesn't)
2. Device has different encryption key than Home Assistant expects
3. Device has encryption, but protocol version mismatch
4. Device firmware is old (Dec 11) without encryption, HA expects new (Dec 12) with encryption

**Missing Documentation:**
1. How does the encryption handshake work in ESPHome Native API?
2. How to verify the device firmware actually has the encryption key loaded?
3. How to check what encryption key the device is using?
4. Can you test connection without encryption first?

**Action Needed:** Document ESPHome API encryption handshake process and troubleshooting.

### 🟡 IMPORTANT: Dec 12 Firmware Flash Status

**What We Know:**
- Firmware compile started on Dec 12
- Config was updated with encryption key
- Docs say device went "offline" after flash

**What We DON'T Know:**
1. Did the USB flash command complete successfully?
2. Was the firmware actually written to the device?
3. Did the device boot after the flash?
4. Were there any error messages during upload?

**Evidence Suggesting Flash Failed:**
- HA storage shows "Dec 11 2025, 20:49:10" compilation time
- If Dec 12 flash succeeded, this should show Dec 12
- Unless HA cached old info

**Action Needed:** Document what happened with Dec 12 flash attempt.

### 🟡 IMPORTANT: Device Recovery (Dec 12 → Dec 13)

**Gap in Documentation:**
The Dec 12 docs say:
- Device not responding to ping
- No serial output
- Completely offline

Dec 13 reality:
- Device IS responding to ping
- USB device exists
- Network communication works

**Missing Information:**
1. Did you power cycle the device between Dec 12 and Dec 13?
2. Did the device self-recover overnight?
3. Did you re-flash again?
4. Did you change any configuration?
5. How did it come back online?

**Action Needed:** Document recovery steps that brought device back online.

### 🟡 IMPORTANT: IP Address Changes

**Timeline:**
- Initially: 192.168.2.12
- Dec 11: Changed to 192.168.2.13
- Current: Still 192.168.2.13

**Why Did IP Change?**
- DHCP lease expired and renewed?
- Device rebooted and got new IP?
- Router reassigned IP?
- Manual change?

**Impact:**
- Home Assistant may have cached old IP
- mDNS should handle this, but cached connections might not

**Missing Documentation:**
1. How to set static IP for ReSpeaker?
2. How to clear Home Assistant's cached device info?
3. Does mDNS automatically update HA, or does HA cache the numeric IP?

**Action Needed:** Document IP address management and Home Assistant caching behavior.

---

## Technical Deep Dive

### ESPHome Native API Encryption

**How It Works (based on research):**
1. Device advertises itself via mDNS with API port (6053)
2. Home Assistant connects to port 6053
3. If encryption enabled:
   - Device sends "hello" with encryption flag
   - Client (HA) must respond with encrypted hello containing shared key
   - If keys match: handshake succeeds, connection established
   - If keys don't match: connection drops immediately

**Our Current Failure:**
```
The connection dropped immediately after encrypted hello
```

This means:
- Step 1-2: ✅ Working (device responding)
- Step 3 hello: ✅ Working (device indicates encryption)
- Step 3 response: ❌ FAILING (key mismatch or device rejects)

**Root Cause Analysis:**
The device firmware is responding to encrypted connections, but rejecting Home Assistant's encryption key. This suggests:

**Theory 1: Device has no encryption key**
- Config file has encryption: ✅ (`key: !secret api_encryption_key`)
- Secrets file has key: ✅ (`api_encryption_key: "<API_ENCRYPTION_KEY>"`)
- Firmware flashed with encryption: ❓ UNCONFIRMED
- Device actually using encryption: ❌ LIKELY NOT

**Theory 2: Device has old firmware (Dec 11)**
- Dec 11 firmware: No encryption
- Dec 12 firmware: With encryption (not confirmed to have flashed successfully)
- HA storage shows: "Dec 11 2025, 20:49:10"
- Conclusion: Device likely running Dec 11 firmware without encryption

**Theory 3: Device has different encryption key**
- Less likely, but possible if device was flashed with different secrets.yaml
- Would need to verify what key is actually in device firmware

### Home Assistant Device Caching

**How HA Stores Device Info:**
- File: `.storage/esphome.01KC92468VWAFR7R2G744W1QTZ`
- Contains: Device info, entity list, compilation time, encryption support
- Updated: When device successfully connects and reports info

**Our Cache Shows:**
```json
"compilation_time": "Dec 11 2025, 20:49:10"
"api_encryption_supported": true
```

**What This Tells Us:**
1. HA connected successfully on Dec 11 at 20:49:10
2. That firmware reported encryption support
3. HA has NOT updated this info since Dec 11
4. Therefore: Device has not successfully connected since Dec 11

**Implications:**
- If Dec 12 flash succeeded, HA doesn't know about it
- HA is trying to use Dec 11 cached info
- But Dec 11 firmware may have claimed encryption support without actually having a key
- This would cause exactly the error we see

---

## Hardware Details

### ReSpeaker XVF3800 + ESP32-S3

**Components:**
1. **ESP32-S3:** Main microcontroller (WiFi, Bluetooth)
   - Dual core, 8MB Flash, 8MB PSRAM
   - Runs ESPHome firmware
   - Handles network communication with Home Assistant
   - Controls LED ring

2. **XMOS XVF3800:** Audio DSP chip
   - 4-microphone array
   - Far-field voice capture
   - Beamforming and echo cancellation
   - Runs separate XMOS firmware v1.0.5
   - Communicates with ESP32-S3 via I2S

3. **LED Ring:** 12 RGB LEDs
   - Controlled by ESP32-S3
   - Configured in ESPHome YAML
   - Should show activity during boot, WiFi connection, voice detection

**LED Ring Behavior (NEEDS DOCUMENTATION):**

Expected behavior based on similar devices:
- **Boot:** Brief flash or animation
- **WiFi connecting:** Slow pulse or rotation
- **WiFi connected:** Brief confirmation pattern then off or dim
- **Idle/Ready:** Dim or off
- **Wake word detected:** Bright flash or animation
- **Listening:** Pulsing or spinning
- **Processing:** Different color/pattern
- **Error:** Red flash or solid red

**Current State:** NO LED activity at all

**Possible Causes:**
1. **Firmware not running:** ESP32-S3 not booting properly
2. **LED disabled in config:** Brightness set to 0 or LEDs disabled
3. **Power issue:** Insufficient power to drive LEDs
4. **Hardware failure:** LED controller issue (less likely)
5. **Config missing:** LED control not compiled into firmware

### USB Connection

**Current Status:**
- Device: `/dev/ttyACM0`
- Type: USB-Serial/JTAG (ESP32-S3 built-in)
- Permissions: `crw-rw----+ 1 root plugdev`
- Last detected: Dec 13 06:05

**What USB Provides:**
1. Power to the board
2. Serial console for logging
3. Programming interface for firmware upload

**Testing USB:**
```bash
# Check if device is detected
ls -la /dev/ttyACM0

# Monitor serial output (if device is booting/running)
screen /dev/ttyACM0 115200
# Or
docker run --rm --device=/dev/ttyACM0 -v "${PWD}":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0
```

**Expected Serial Output (if working):**
```
[I][app:029]: Running through setup()...
[I][wifi:029]: WiFi Connecting to '<WIFI_SSID>'...
[I][wifi:399]: WiFi Connected!
[I][api:025]: API Server initialized
[I][xvf:123]: XMOS firmware v1.0.5
```

**Current Serial Output:** Not tested yet (attempted command had syntax error)

---

## Current Configuration

### ESPHome Config
**File:** `/home/stewartalsop/prototypes/home-assistant/esphome/respeaker.yaml`
**Lines 117-121:** API configuration
```yaml
api:
  id: api_id
  encryption:
    key: !secret api_encryption_key
```

### Secrets File
**File:** `/home/stewartalsop/prototypes/home-assistant/esphome/secrets.yaml`
```yaml
wifi_ssid: "<WIFI_SSID>"
wifi_password: "<WIFI_PASSWORD>"
ota_password: "<OTA_PASSWORD>"
api_encryption_key: "<API_ENCRYPTION_KEY>"
```

**Key Details:**
- Format: Base64-encoded 32 bytes
- Generated: 2025-12-11
- Method: `python3 -c "import base64, secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())"`

### Network Configuration
```
Raspberry Pi:     192.168.2.65
  - Home Assistant:  port 8123
  - ESPHome Dashboard: port 6052

ReSpeaker:        192.168.2.13
  - ESPHome API:   port 6053 (encrypted)
  - mDNS name:     respeaker-xvf3800-assistant.local

WiFi Network:     <WIFI_SSID>
Router:           (IP unknown)
```

---

## Diagnostic Procedures

### 1. Check Device Serial Output

**Purpose:** See what the device is actually doing during boot and runtime.

```bash
cd /home/stewartalsop/prototypes/home-assistant/esphome

# Via ESPHome (preferred)
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0

# Or via screen (manual)
screen /dev/ttyACM0 115200
# Exit screen: Ctrl+A, then K, then Y
```

**What to Look For:**
- Boot messages: "Running through setup()"
- WiFi: "WiFi Connected!" and IP address
- XMOS: "XMOS firmware v1.0.5"
- API: "API Server initialized" or "API encryption key set"
- Errors: Any red error messages

### 2. Verify Firmware Compilation Time

**Purpose:** Check if device is running Dec 11 or Dec 12 firmware.

**Method 1: Via Serial Logs**
Look for line like: `[I][app:029]: Application compiled on Dec XX 2025, XX:XX:XX`

**Method 2: Via Home Assistant**
Check device info page - but this may be cached

**Method 3: Via ESPHome API (if working)**
```bash
# If API was working, you could query:
curl http://192.168.2.13:6053/...
# But API is not working, so this won't help
```

### 3. Test Without Encryption

**Purpose:** Rule out encryption as the problem.

**Steps:**
1. Edit `respeaker.yaml` - comment out encryption:
```yaml
api:
  id: api_id
  # encryption:
  #   key: !secret api_encryption_key
```

2. Recompile and flash firmware
3. In Home Assistant, remove device
4. Re-add device WITHOUT encryption key
5. Test if connection works

**If this works:** Encryption was the problem, need to properly flash firmware with encryption
**If this fails:** Problem is deeper than encryption

### 4. Full Firmware Re-Flash

**Purpose:** Ensure device is running current firmware with encryption.

**Method: USB Upload (most reliable)**
```bash
cd /home/stewartalsop/prototypes/home-assistant/esphome

# Compile firmware
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome compile respeaker.yaml

# Upload via USB
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome upload respeaker.yaml --device /dev/ttyACM0
```

**Watch for:**
- Compilation completes without errors
- Upload shows progress: "Writing at 0x00010000... (X %)"
- Upload completes: "Hash of data verified"
- Device boots: Serial output shows boot messages

### 5. Home Assistant Integration Reset

**Purpose:** Clear cached device info and establish fresh connection.

**Steps:**
1. In Home Assistant UI:
   - Settings → Devices & Services
   - Find ESPHome integration
   - Click on ReSpeaker device
   - Click 3-dot menu → Delete Device
   - Confirm deletion

2. Wait 30 seconds

3. Add device fresh:
   - Settings → Devices & Services
   - Click "+ ADD INTEGRATION"
   - Search "ESPHome"
   - Host: `192.168.2.13` or `respeaker-xvf3800-assistant.local`
   - Encryption key: `<API_ENCRYPTION_KEY>`
   - Submit

**Expected Result:**
- Device connects successfully
- Entities populate with current values (not "Unavailable")
- LED ring shows activity

---

## Recommended Next Steps

### Immediate Actions (in order)

**Step 1: Check Serial Output**
- Connect to device via USB serial
- See what's actually happening during boot
- Confirm device is running and what firmware version
- **Why:** We need to know if device is even booting properly

**Step 2: Verify Firmware Flash Status**
- Check serial logs for compilation date/time
- Confirm if Dec 12 flash actually succeeded
- **Why:** HA shows Dec 11 firmware, need to confirm what device has

**Step 3: Re-flash Firmware (if needed)**
- If device has Dec 11 firmware, flash Dec 12 with encryption
- Use USB upload for reliability
- Monitor serial output to confirm success
- **Why:** Need device to have encryption key matching HA config

**Step 4: Reset Home Assistant Integration**
- Delete device from Home Assistant
- Re-add with correct IP and encryption key
- **Why:** Clear any cached info that doesn't match current device

**Step 5: Test LED Control**
- Once connected, try changing LED brightness via HA
- Verify LEDs respond to commands
- **Why:** Confirm LED ring is functional

### Long-term Actions

**Document LED Behavior**
- Create visual reference for normal LED patterns
- Document what each pattern means
- Create troubleshooting guide for LED issues

**Implement Static IP**
- Configure DHCP reservation on router for MAC 9C:13:9E:AD:0F:50
- Or set static IP in ESPHome config
- Prevents IP changes that confuse Home Assistant

**Set Up Monitoring**
- Create Home Assistant automation to alert if device goes offline
- Log connection errors for debugging
- Regular checks of device status

**Create Backup Plan**
- Document working firmware configuration
- Save compiled .bin files for quick recovery
- Document flash procedures for future reference

---

## Known Limitations & Workarounds

### Docker Add-ons Not Available
**Issue:** Home Assistant Docker installation doesn't support add-ons
**Impact:** Cannot use HA's built-in voice assistant processing
**Workaround:** Use VAPI (external voice AI service) instead
**Status:** Planned, not yet implemented

### OTA Upload Failures
**Issue:** Over-the-air firmware updates don't always work
**Impact:** Can't update firmware without USB connection
**Workaround:** Always use USB for firmware uploads
**Status:** Ongoing issue

### IP Address Changes
**Issue:** Device IP changes after reboots (DHCP)
**Impact:** Home Assistant loses connection when IP changes
**Workaround:** Use mDNS hostname or set up static IP
**Status:** Not yet implemented

---

## Error Messages Reference

### "The connection dropped immediately after encrypted hello"
**Full Error:**
```
Can't connect to ESPHome API for respeaker-xvf3800-assistant @ 192.168.2.13:
The connection dropped immediately after encrypted hello;
Try enabling encryption on the device or turning off encryption on the client
(EncryptionHelloAPIError)
```

**Meaning:**
- Home Assistant tried to connect with encryption
- Device responded but rejected the encrypted hello
- Most likely cause: encryption keys don't match
- Or: device doesn't actually have encryption enabled in firmware

**Solution:**
1. Verify device firmware has encryption key
2. Verify HA config has matching encryption key
3. Re-flash device firmware if needed
4. Reset HA integration with correct key

### "Socket operation failed BAD_INDICATOR errno=11"
**Full Error:**
```
[W][api.connection:1889]: 192.168.2.65 (192.168.2.65): Socket operation failed BAD_INDICATOR errno=11
```

**Meaning:**
- errno=11 = EAGAIN = "Resource temporarily unavailable"
- Socket read/write operation couldn't complete immediately
- Usually indicates timing issue or buffer problem

**Context:**
- This was from Dec 11, before encryption was added
- May be unrelated to current encryption issue
- Suggests network/timing issues between Docker containers

**Solution:**
- Less relevant now that we have specific encryption error
- But if it recurs: check network latency, Docker networking config

### "Timeout waiting for HelloResponse"
**Full Error:**
```
WARNING [aioesphomeapi.reconnect_logic]
Can't connect to ESPHome API for respeaker-xvf3800-assistant @ 192.168.2.13:
Timeout waiting for HelloResponse after 30.0s (TimeoutAPIError)
```

**Meaning:**
- Home Assistant connected to port 6053
- Sent initial "hello" request
- No response within 30 seconds
- Device not responding at all

**Context:**
- Appeared in logs on Dec 12
- Suggests device was not running or API not responding
- Different from "encrypted hello" error which shows device IS responding

**Solution:**
- Check if device is booting properly
- Verify API is enabled in config
- Check if port 6053 is actually open

---

## Files & Locations Reference

### Configuration Files
```
/home/stewartalsop/prototypes/home-assistant/
├── docker-compose.yml              # Container definitions
├── README.md                       # Quick reference
├── config/                         # Home Assistant config
│   └── .storage/
│       └── esphome.01KC92468...    # Device cache (DO NOT EDIT MANUALLY)
├── esphome/                        # ESPHome configs
│   ├── respeaker.yaml              # Main device config (1757 lines)
│   └── secrets.yaml                # WiFi, passwords, encryption key
└── docs/                           # Documentation
    ├── setup-2025-12-11.md         # Initial setup guide
    ├── troubleshooting-2025-12-11.md  # Troubleshooting guide
    ├── current-status-2025-12-11.md   # Old status (outdated)
    └── current-status-2025-12-13.md   # This file (current)
```

### Compiled Firmware (when built)
```
/home/stewartalsop/prototypes/home-assistant/esphome/.esphome/build/
└── respeaker-xvf3800-assistant/
    └── .pioenvs/respeaker-xvf3800-assistant/
        ├── firmware.bin            # Main firmware file
        ├── firmware.ota.bin        # OTA update format
        └── firmware.factory.bin    # Full flash image
```

### Log Files
```
# Home Assistant logs
docker logs homeassistant

# ESPHome dashboard logs
docker logs esphome

# Device logs (via USB)
/dev/ttyACM0 (115200 baud)

# Device logs (via network - if API working)
ESPHome logs command
```

---

## Quick Reference Commands

### Device Status
```bash
# Check if device is online
ping -c 3 192.168.2.13

# Check if USB connected
ls -la /dev/ttyACM0

# View device logs
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0
```

### Firmware Management
```bash
cd /home/stewartalsop/prototypes/home-assistant/esphome

# Validate config
docker run --rm \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome config respeaker.yaml

# Compile firmware
docker run --rm \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome compile respeaker.yaml

# Upload via USB
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome upload respeaker.yaml --device /dev/ttyACM0

# Upload via OTA (device must be online)
docker run --rm \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome run respeaker.yaml --device 192.168.2.13
```

### Home Assistant Management
```bash
# View logs
docker logs homeassistant -f

# Filter for ReSpeaker/ESPHome
docker logs homeassistant 2>&1 | grep -i "respeaker\|esphome"

# Restart Home Assistant
cd /home/stewartalsop/prototypes/home-assistant
docker compose restart homeassistant

# Check if HA can reach device
docker exec homeassistant ping -c 3 192.168.2.13
```

---

## Access URLs

- **Home Assistant:** http://192.168.2.65:8123
- **ESPHome Dashboard:** http://192.168.2.65:6052
- **ReSpeaker Device:** http://192.168.2.13 (if web server enabled - currently not)
- **ReSpeaker mDNS:** http://respeaker-xvf3800-assistant.local

---

## External References

- **FormatBCE Integration GitHub:** https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration
- **ESPHome API Docs:** https://esphome.io/components/api.html
- **ESPHome Voice Assistant:** https://esphome.io/components/voice_assistant.html
- **Seeed Studio Wiki:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_home_assistant/
- **Home Assistant Community Thread:** https://community.home-assistant.io/t/respeaker-xmos-xvf3800-esphome-integration/927241

---

## Summary for Quick Resume

**Goal:** Integrate ReSpeaker XVF3800 voice hardware with Home Assistant, then route to VAPI for voice AI.

**Current Blocker:** Device firmware and Home Assistant have mismatched encryption keys. Device is online and responding but encryption handshake fails immediately.

**Most Likely Root Cause:** Dec 12 firmware flash did not complete successfully. Device is still running Dec 11 firmware which doesn't have the encryption key, but Home Assistant expects it to have encryption.

**Next Action:** Check serial output to confirm firmware version, then re-flash firmware via USB with encryption key, then reset Home Assistant integration with fresh connection.

**Quick Recovery Command:**
```bash
# 1. Check what's running
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0

# 2. Re-flash firmware
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome run respeaker.yaml --device /dev/ttyACM0

# 3. In Home Assistant: Delete device, re-add with IP 192.168.2.13 and key
```

**Encryption Key:** `<API_ENCRYPTION_KEY>`

---

*Last Updated: 2025-12-13 06:10*
*Next Update: After completing serial output check and firmware re-flash*
