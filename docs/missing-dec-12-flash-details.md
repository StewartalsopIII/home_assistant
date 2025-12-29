# Missing Information: Dec 12 Firmware Flash

**Date:** 2025-12-13
**Status:** Critical gap in timeline - need to reconstruct what happened

---

## The Gap

### What We Know
From the Anki documentation provided, we know:
1. Firmware re-flash was **attempted** on Dec 12
2. Goal was to flash firmware with encryption key
3. After the flash attempt, device was reported as "offline"
4. User noted device went "completely unresponsive"

### What We DON'T Know
1. **Did the flash command complete successfully?**
2. **Were there any error messages during upload?**
3. **Did the device reboot after flash?**
4. **What method was used? (USB or OTA?)**
5. **How long did the flash take?**
6. **Was success message displayed?**
7. **What happened immediately after?**

This is a **critical gap** because:
- If flash succeeded: Device should have encryption, but HA shows Dec 11 compile time
- If flash failed: Device still has old firmware, which matches HA's Dec 11 cache
- We don't know which is true

---

## Evidence Analysis

### Evidence Suggesting Flash FAILED

**Evidence 1: Home Assistant Cache Shows Dec 11**
```json
"compilation_time": "Dec 11 2025, 20:49:10"
```
- HA storage file shows Dec 11 compilation time
- If Dec 12 flash succeeded, device would report new compile time
- But HA cache only updates when device successfully connects
- So this could mean:
  - Flash failed, device still has Dec 11 firmware, OR
  - Flash succeeded, but device never connected to HA to update cache

**Evidence 2: Device Went "Offline" After Flash**
- Dec 12 docs say device stopped responding to ping
- Suggests flash may have failed or corrupted firmware
- Or device stuck in boot loop

**Evidence 3: Current Encryption Error**
- "Connection dropped after encrypted hello"
- Suggests device doesn't have encryption key
- Dec 11 firmware didn't have encryption
- Consistent with flash failing and device reverting to Dec 11

**Evidence 4: No Serial Output Reported**
- Dec 12 docs say no USB serial output
- If firmware flashed successfully, there should be boot messages
- No serial suggests firmware not running or corrupted

### Evidence Suggesting Flash SUCCEEDED (or Partial Success)

**Evidence 1: Device Came Back Online**
- Dec 13: Device responds to ping at 192.168.2.13
- Suggests device recovered somehow
- But unclear how or when

**Evidence 2: Device Responds on API Port**
- HA can initiate handshake (gets to "encrypted hello")
- Means API is running and responding
- If flash totally failed, might not respond at all

**Evidence 3: IP Changed to .13**
- Dec 11: Device was at 192.168.2.12
- Dec 12+: Device at 192.168.2.13
- IP change suggests device rebooted and got new DHCP lease
- Could indicate successful flash and reboot
- Or could indicate multiple failed boots causing multiple DHCP requests

### Evidence Requiring Explanation

**Problem 1: Timeline Gap**
- Dec 12 evening: Device offline
- Dec 13 morning: Device online
- What happened in between?
  - Did user take action?
  - Did device self-recover?
  - Was another flash attempted?
  - Did user power cycle?

**Problem 2: HA Compilation Time**
- Shows Dec 11, not Dec 12
- But we attempted flash on Dec 12
- Possible explanations:
  1. Flash failed, device still has Dec 11 firmware
  2. Flash succeeded but HA never connected to see new firmware
  3. HA cached old data and hasn't refreshed
  4. Device is running Dec 12 firmware but compile time wasn't updated in code

**Problem 3: LED Behavior Change**
- Before: "Blinking strongly for weeks"
- After Dec 12: No LED activity at all
- This change happened around the flash attempt
- Suggests something changed in firmware or config
- But unclear if related to flash or something else

---

## What Should Have Been Documented

### During Flash Attempt (Dec 12)

**Before Starting Flash:**
- Current device state (online, IP address, responding)
- Firmware version currently running
- Last known-good state

**Flash Command Used:**
```bash
# Which command was run? Examples:
docker run --rm --device=/dev/ttyACM0 \
  -v "${PWD}":/config ghcr.io/esphome/esphome \
  run respeaker.yaml --device /dev/ttyACM0

# Or OTA?
docker run --rm -v "${PWD}":/config \
  ghcr.io/esphome/esphome run respeaker.yaml --device 192.168.2.12
```

**During Flash:**
- Compilation phase: Did it complete? Any errors?
- Upload phase: Did it start? Progress shown?
- Any error messages at any point?
- How long did it take?

**Expected Output (USB flash):**
```
INFO Reading configuration respeaker.yaml...
INFO Compiling... (this takes several minutes)
INFO Compiling finished!
INFO Looking for upload port...
INFO Uploading binary...
Chip is ESP32-S3 (revision v0.2)
...
Writing at 0x00010000... (5 %)
Writing at 0x00020000... (10 %)
...
Writing at 0x002f0000... (100 %)
...
Hash of data verified.
Hard resetting via RTS pin...
INFO Successfully uploaded firmware.
```

**After Flash:**
- Was "Successfully uploaded firmware" message shown?
- Did device reboot? (should see serial output restart)
- Did device reconnect to WiFi?
- What was new IP address?
- Could ping device?
- Could connect to API?

### Recovery Process (Dec 12 → Dec 13)

**What Actions Were Taken:**
- Did you power cycle the device?
- Did you try different USB port?
- Did you try different USB cable?
- Did you wait X minutes/hours?
- Did you restart any containers?
- Did you modify any config files?
- Did you attempt another flash?

**Device State Changes:**
- When did device start responding to ping again?
- Did LEDs ever turn on during recovery?
- Did you see any serial output at any point?
- When did Home Assistant detect device?

---

## Critical Questions That Need Answers

### About the Dec 12 Flash

**Q1: What exact command was used for flashing?**
- USB or OTA method?
- Full command with all parameters?

**Q2: Did compilation phase complete successfully?**
- Look for: "INFO Compiling finished!"
- Any errors during compilation?
- Compilation time (should be ~11 minutes)

**Q3: Did upload phase start?**
- Look for: "INFO Uploading binary..."
- Or: "INFO Starting upload..."

**Q4: Was there upload progress shown?**
- Percentage indicators?
- Memory address ranges being written?

**Q5: Did upload complete?**
- Look for: "INFO Successfully uploaded firmware"
- Or: "Hash of data verified"

**Q6: Were there any error messages?**
- At compilation?
- During upload?
- After upload?

**Q7: Did device reboot after flash?**
- Would see serial output restart
- Boot messages would appear

**Q8: How long did the entire process take?**
- Compile: ~11 minutes (known)
- Upload: 1-3 minutes typical
- Total: ~15 minutes if successful

### About Recovery (Dec 12 → Dec 13)

**Q9: When did you notice device was offline?**
- Immediately after flash?
- Or some time later?

**Q10: How long was device offline?**
- Minutes? Hours? Overnight?

**Q11: What troubleshooting was attempted?**
- Power cycle?
- Different USB port?
- Container restart?
- Config changes?

**Q12: When/how did device come back online?**
- Specific action that brought it back?
- Or spontaneous recovery?

**Q13: What's the first indication it was back online?**
- Ping response?
- LED activity?
- Home Assistant detection?
- Serial output?

**Q14: Has device been stable since coming back?**
- Continuous uptime?
- Or intermittent?

---

## How to Reconstruct Events

### Method 1: Check System Logs
```bash
# Docker logs might show flash attempt
docker logs esphome --since "2025-12-12T00:00:00" > esphome-dec12.log

# Check for compilation/upload messages
grep -i "compil\|upload\|success\|error" esphome-dec12.log

# System journal might have USB events
journalctl --since "2025-12-12 00:00:00" --until "2025-12-13 06:00:00" | grep -i "ttyACM\|usb"
```

### Method 2: Check Bash History
```bash
# Review commands run on Dec 12
history | grep -i "2025-12-12\|docker run\|esphome"

# Look for flash commands
history | grep "esphome.*run\|esphome.*upload"
```

### Method 3: Check File Timestamps
```bash
# When was firmware last compiled?
ls -la ~/prototypes/home-assistant/esphome/.esphome/build/respeaker*/

# When were config files last modified?
ls -la ~/prototypes/home-assistant/esphome/*.yaml
```

### Method 4: Check Device Serial Output Now
```bash
# Connect to device and look for compile time in logs
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0

# Look for line like:
# [I][app:xxx]: Application compiled on Dec XX 2025, XX:XX:XX
```

---

## Possible Scenarios

### Scenario A: Flash Failed, Device Recovered
**What Happened:**
1. Dec 12: Started flash process
2. Flash failed partway through (error, interrupted, etc.)
3. Device left in bad state (corrupted firmware or boot loop)
4. Device offline for hours
5. Dec 13: Device somehow recovered (watchdog reset?)
6. Device now running old Dec 11 firmware

**Evidence Supporting:**
- HA shows Dec 11 compile time
- Device behaves like Dec 11 firmware (no encryption)
- Device went offline then recovered

**Evidence Against:**
- Device came back online somehow (usually requires manual intervention)
- IP changed (suggests successful boot, not recovery from crash)

### Scenario B: Flash Succeeded, HA Not Updated
**What Happened:**
1. Dec 12: Flash completed successfully
2. Device rebooted with new firmware
3. Device came online at new IP (.13)
4. But device has wrong encryption key or config issue
5. Device never successfully connected to HA
6. HA cache never updated from Dec 11

**Evidence Supporting:**
- Device responds on API port (suggesting API is running)
- Device handles encrypted hello (suggesting encryption code present)
- IP changed (suggests successful reboot with new firmware)

**Evidence Against:**
- Device reports offline after flash (wouldn't be if successful)
- Encryption error suggests no key (but Dec 12 firmware should have key)
- HA shows Dec 11 (but this could be just cache)

### Scenario C: Flash Partially Succeeded
**What Happened:**
1. Dec 12: Flash wrote some but not all new firmware
2. Device rebooted with corrupted or mixed firmware
3. Device in weird state: some new code, some old code
4. Can boot and connect to network (old code)
5. But encryption broken (partially new code)
6. LEDs broken (corrupted firmware)

**Evidence Supporting:**
- Device works partially (network yes, encryption no)
- LED behavior changed (firmware changed somehow)
- Strange errors that don't quite make sense

**Evidence Against:**
- ESP32 has flash verification (shouldn't boot corrupted firmware)
- More complex explanation than needed

### Scenario D: Wrong Firmware Flashed
**What Happened:**
1. Dec 12: Flash succeeded
2. But flashed wrong version or config
3. Maybe flashed Dec 11 firmware again by mistake?
4. Or flashed with wrong secrets.yaml?
5. Device running firmware, but not the expected one

**Evidence Supporting:**
- Device works (network, ping, API responding)
- But encryption doesn't match (wrong key?)
- Compile time matches Dec 11 (if re-flashed Dec 11)

**Evidence Against:**
- Would require user error (unlikely, command should have compiled current config)

---

## Action Items

### Immediate: Determine Current Firmware
**Method:** Check serial output for compilation date
```bash
docker run --rm --device=/dev/ttyACM0 \
  -v "/home/stewartalsop/prototypes/home-assistant/esphome":/config \
  ghcr.io/esphome/esphome logs respeaker.yaml --device /dev/ttyACM0
```

**Look for:**
```
[I][app:xxx]: Application compiled on Dec XX 2025, XX:XX:XX
```

**If says Dec 11:** Flash failed or never completed
**If says Dec 12:** Flash succeeded, but something else wrong
**If says other date:** Unexpected, need to investigate

### Secondary: Review Available Logs
**Check Docker logs:**
```bash
docker logs esphome --since "2025-12-12T00:00:00" --until "2025-12-13T00:00:00"
```

**Check bash history:**
```bash
history | grep "2025-12-12"
```

**Check system journal:**
```bash
journalctl --since "2025-12-12" --until "2025-12-13"
```

### Tertiary: Document Current State
Before attempting anything else:
1. Document current device behavior (what works, what doesn't)
2. Back up current configs
3. Document current HA state
4. Then proceed with troubleshooting

---

## What This Means for Next Steps

### If Flash Failed (Dec 11 firmware running)
**Action:** Re-flash firmware properly
**Expected Result:** Device will have encryption, connect to HA
**Risk:** Low - device already running old firmware

### If Flash Succeeded (Dec 12 firmware running)
**Action:** Debug why encryption failing despite being in firmware
**Expected Result:** Find config mismatch, fix, reconnect
**Risk:** Medium - may need to re-flash anyway

### If Unknown
**Action:** Must determine firmware version first
**Expected Result:** Can then choose appropriate next step
**Risk:** None - just information gathering

---

## Lessons for Future Flashing

### Before Flash:
1. Document current state completely
2. Back up working config
3. Verify config compiles without errors
4. Note current IP, firmware version, device state

### During Flash:
1. **Capture all output** to log file:
```bash
docker run ... 2>&1 | tee flash-$(date +%Y%m%d-%H%M%S).log
```

2. **Watch for specific messages:**
   - "Compiling finished"
   - "Uploading binary"
   - "Successfully uploaded"
   - Any errors

3. **Don't interrupt the process**
   - Full flash takes 15+ minutes
   - Wait for "Successfully uploaded" before doing anything

### After Flash:
1. **Wait for device to boot** (30-60 seconds)
2. **Check serial output** - confirm boot messages
3. **Verify WiFi connection** - ping test
4. **Verify API** - HA connection test
5. **Test basic functions** - LED, audio, etc.
6. **Document results** - success or failure, with details

---

## Summary

The Dec 12 flash attempt is a **critical undocumented event**. We don't know:
- If it succeeded
- What errors occurred
- How device recovered
- What firmware is actually running now

**This is the KEY QUESTION** that determines our next steps.

**Priority Action:** Check serial output to see firmware compile date. This single piece of information will tell us which scenario we're in and what to do next.

**Once we know:** We can either:
1. Re-flash properly (if flash failed)
2. Debug encryption (if flash succeeded)
3. Investigate deeper (if something unexpected)

But we cannot proceed intelligently without knowing what firmware is currently running.

---

*Update this document once we determine firmware version from serial output.*
