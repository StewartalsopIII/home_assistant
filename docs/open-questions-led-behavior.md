# Open Questions: LED Behavior & Diagnostics

**Date:** 2025-12-13
**Status:** Critical symptom requiring investigation

---

## Primary Question: Why Are LEDs Not Blinking?

### Symptom Description
- **Current State:** ReSpeaker XVF3800 LED ring shows NO activity whatsoever
- **Previous State:** LEDs were "blinking strongly for weeks" before
- **Context:** Device plugged into USB to Raspberry Pi, device responds to ping

### Critical Nature
The LED ring is usually the primary visual indicator of device status. No LED activity could indicate:
1. Severe problem (device not booting, firmware crashed)
2. Minor issue (LED control disabled, brightness set to 0)
3. Configuration change (LEDs intentionally disabled)

**We cannot determine which without investigation.**

---

## Undocumented: Expected LED Behavior

### What SHOULD the LED Ring Do?

Based on similar voice assistant devices (needs confirmation for ReSpeaker XVF3800):

#### During Boot Sequence
- **Expected:** Brief flash, sweep pattern, or boot animation
- **Duration:** 2-5 seconds
- **Color:** Often white or multi-color
- **Purpose:** Indicates ESP32-S3 is booting and initializing

#### WiFi Connection Process
- **Expected:** Slow pulse, rotating pattern, or breathing effect
- **Duration:** 5-30 seconds (while connecting)
- **Color:** Often blue or yellow
- **Purpose:** Shows device is attempting to connect to WiFi

#### WiFi Connected
- **Expected:** Brief confirmation pattern (flash, sweep, etc.)
- **Duration:** 1-2 seconds
- **Color:** Often green or steady color
- **Purpose:** Confirms successful WiFi connection

#### Idle/Ready State
- **Expected:** Dim glow, single LED lit, or completely off
- **Duration:** Continuous until event occurs
- **Color:** Often dim white, blue, or off
- **Purpose:** Shows device is ready and waiting for wake word

#### Wake Word Detected
- **Expected:** Bright flash, rapid spin, or radial pattern
- **Duration:** < 1 second
- **Color:** Often bright white or blue
- **Purpose:** Confirms wake word was heard

#### Listening for Command
- **Expected:** Pulsing, breathing, or spinning animation
- **Duration:** While listening (5-10 seconds)
- **Color:** Often blue or cyan
- **Purpose:** Shows device is actively listening

#### Processing Command
- **Expected:** Different pattern (dots, thinking animation)
- **Duration:** While processing
- **Color:** Often different from listening (purple, yellow)
- **Purpose:** Shows command is being processed

#### Speaking/Playing Response
- **Expected:** Pattern synchronized with audio output
- **Duration:** While audio playing
- **Color:** Often changes with audio levels
- **Purpose:** Visual feedback that audio is playing

#### Error State
- **Expected:** Red flash, solid red, or specific error pattern
- **Duration:** Brief flash or continuous until resolved
- **Color:** Red
- **Purpose:** Indicates error or problem

#### Muted State
- **Expected:** Red LED(s), different pattern, or off
- **Duration:** While muted
- **Color:** Often red or orange
- **Purpose:** Shows microphone is muted

### Current Reality
**NO LED activity in ANY state** - This is abnormal.

---

## Questions Requiring Answers

### Hardware Questions

**Q1: Is the LED ring receiving power?**
- Method: Visual inspection (difficult to test without opening case)
- Method: Multimeter test on LED power pins
- Method: Check power consumption of device (with vs without LEDs)

**Q2: Are the LED control pins connected correctly?**
- Check: ESPHome config for LED pin definitions
- Check: Hardware datasheet for correct pins
- Check: Any recent config changes to LED pins

**Q3: Is there a hardware switch or jumper for LEDs?**
- Check: ReSpeaker XVF3800 documentation
- Check: Physical board for switches/jumpers
- Check: Schematic if available

### Firmware Questions

**Q4: Is LED control enabled in the firmware?**
- Check: `respeaker.yaml` for LED configuration
- Check: If LED component is commented out or disabled
- Check: If LED component failed to compile

**Q5: What LED driver/library is being used?**
- Check: ESPHome config for LED platform (WS2812, APA102, etc.)
- Check: Compilation logs for LED component initialization
- Verify: Correct LED type specified for this hardware

**Q6: Is LED brightness set to minimum/zero?**
- Check: Default brightness in config
- Check: Current brightness via Home Assistant (if connected)
- Check: If brightness can be changed via API

**Q7: Did firmware compilation include LED support?**
- Check: Compilation logs for LED component
- Check: Binary size (LEDs add significant size)
- Check: If any LED-related errors during compile

### Configuration Questions

**Q8: Where is LED configuration in respeaker.yaml?**
- Need: Line numbers and section details
- Need: Current configuration values
- Need: Default vs customized settings

**Q9: Are LEDs controlled by ESP32-S3 or XMOS chip?**
- Check: Hardware documentation
- Check: ESPHome config structure
- Important: Determines where to troubleshoot

**Q10: Can LEDs be tested independently?**
- Method: ESPHome API call to set color
- Method: Home Assistant automation
- Method: Direct firmware command

### State Questions

**Q11: Does "no LED" mean firmware isn't running?**
- If firmware runs but LED code fails: Other functions might work
- If firmware doesn't boot: Nothing would work (but ping works!)
- Need: Serial output to confirm firmware is running

**Q12: Can device function normally without LEDs?**
- Yes, if LED control is separate from core functionality
- Core functions: WiFi, API, audio, wake word detection
- LED is visual feedback only

**Q13: Did LED config change between Dec 11 and Dec 12?**
- Check: Git history or backup of config
- Check: If encryption addition affected LED section
- Review: Any intentional or accidental LED changes

### Diagnostic Questions

**Q14: How do we test if LEDs are functional?**
**Via Home Assistant (if connected):**
```yaml
# In HA Developer Tools → Services
service: esphome.respeaker_xvf3800_assistant_set_led_color
data:
  red: 255
  green: 0
  blue: 0
```

**Via ESPHome API (if accessible):**
```bash
# Requires working API connection
# Would call the set_led_color action
```

**Via Direct Config Test:**
- Create minimal config with just LED test
- Flash to device
- Observe if LEDs respond

**Q15: What do serial logs say about LEDs?**
Look for:
```
[I][light:xxx]: Setting up light 'LED Ring'...
[I][light:xxx]: Light 'LED Ring' initialized
[E][light:xxx]: Failed to initialize light
```

**Q16: Is there a boot mode that disables LEDs?**
- Safe mode?
- Recovery mode?
- Low-power mode?

---

## Investigation Plan

### Phase 1: Confirm Firmware is Running
**Goal:** Determine if firmware is actually running or if device is stuck.

**Steps:**
1. Connect to serial console (`/dev/ttyACM0`)
2. Power cycle device (unplug/replug USB)
3. Watch boot sequence
4. Look for:
   - Boot messages
   - WiFi connection
   - XMOS initialization
   - LED initialization messages
   - Any error messages

**Expected Output (if working):**
```
[I][app:029]: Running through setup()...
[I][wifi:029]: WiFi Connecting to '<WIFI_SSID>'...
[I][wifi:399]: WiFi Connected!
[I][api:025]: API Server initialized
[I][light:xxx]: Setting up light 'LED Ring'...
[I][xvf:123]: XMOS firmware v1.0.5
```

**If No Serial Output:**
- Firmware not running or crashed
- Serial console not configured
- Wrong baud rate (try 115200, 9600)

### Phase 2: Check LED Configuration
**Goal:** Verify LED control is present and correct in config.

**Steps:**
1. Read `respeaker.yaml` LED section
2. Identify LED component type (WS2812, APA102, etc.)
3. Verify pin assignments
4. Check brightness settings
5. Look for any disabled or commented sections

**Key Config Sections to Check:**
```yaml
# LED Ring definition
light:
  - platform: ...
    name: "LED Ring"
    ...

# LED effects
effects:
  - ...

# LED brightness control
number:
  - platform: template
    name: "LED Ring Brightness"
    ...
```

### Phase 3: Verify Firmware Compilation
**Goal:** Confirm LED code was compiled into firmware.

**Steps:**
1. Review compilation logs from Dec 11 and Dec 12 builds
2. Look for LED component messages
3. Check firmware size (LEDs add ~50-100KB typically)
4. Verify no compilation errors in LED section

### Phase 4: Test LED Control
**Goal:** Attempt to directly control LEDs.

**Method 1: Via Home Assistant** (requires working connection)
1. Go to Developer Tools → Services
2. Find `esphome.respeaker_xvf3800_assistant_set_led_color`
3. Call with: `red: 255, green: 0, blue: 0`
4. Observe if LEDs light up

**Method 2: Via Config Change**
1. Edit config to set default brightness high
2. Set default color to bright white
3. Re-flash firmware
4. See if LEDs come on at boot

**Method 3: Via Minimal Test Config**
1. Create simple config with just WiFi + LEDs
2. Flash to device
3. LEDs should light up immediately
4. Isolates LED issue from other components

### Phase 5: Hardware Verification
**Goal:** Rule out hardware failure.

**Steps:**
1. Visual inspection of LED ring
2. Check for physical damage
3. Try different USB power source (rule out power issue)
4. Check voltage at LED power pins (if accessible)

---

## Specific Config Areas to Document

### LED Configuration in respeaker.yaml

**Need to document:**
1. **Line numbers:** Where is LED config located?
2. **Platform type:** WS2812B, APA102, or other?
3. **Pin assignment:** Which GPIO pin controls LEDs?
4. **Number of LEDs:** How many in the ring? (likely 12)
5. **Default state:** On/off, color, brightness at boot
6. **Effects defined:** What animations are available?
7. **Control entities:** What HA entities control LEDs?

**Example of what we need:**
```yaml
# Lines XXX-YYY
light:
  - platform: fastled_clockless  # or neopixel, or spi
    chipset: WS2812B
    pin: GPIO48  # Example pin
    num_leds: 12
    rgb_order: GRB
    name: "LED Ring"
    id: led_ring
    default_transition_length: 0s
    restore_mode: ALWAYS_OFF  # Could be issue if set to OFF
    effects:
      - addressable_rainbow:
      - ...
```

### LED Control in Home Assistant

From the HA storage file, we know these entities exist:
```
number.respeaker_led_ring_brightness
select.respeaker_led_ring_color_preset
```

**Need to document:**
1. Current brightness value (is it 0?)
2. Current color preset selection
3. Are these entities working (or also "Unavailable")?
4. What are the available color presets?

---

## Possible Root Causes (Ranked by Likelihood)

### 1. Brightness Set to Zero (Medium-High Likelihood)
**Symptoms Match:** Device working but LEDs off
**Why:** User or automation may have set brightness to 0
**How to Check:** Serial logs or HA entity state
**How to Fix:** Increase brightness via HA or config

### 2. LEDs Disabled in Config (Medium Likelihood)
**Symptoms Match:** Device working, no LED activity
**Why:** Config change during encryption addition
**How to Check:** Review respeaker.yaml
**How to Fix:** Re-enable LEDs, re-flash

### 3. Firmware Not Running (Medium Likelihood)
**Symptoms Match:** No LEDs, but ping works
**Why:** Boot loop, crash after WiFi connect
**How to Check:** Serial output
**How to Fix:** Reflash firmware, check for errors

### 4. LED Code Failed to Compile (Low-Medium Likelihood)
**Symptoms Match:** Device works but LEDs don't
**Why:** Compilation error in LED section
**How to Check:** Compilation logs
**How to Fix:** Fix config error, recompile

### 5. Power Insufficient for LEDs (Low Likelihood)
**Symptoms Match:** Device works but LEDs don't light
**Why:** USB power insufficient for 12 bright LEDs
**How to Check:** Try external power, lower brightness
**How to Fix:** Use powered USB hub or external supply

### 6. Hardware LED Failure (Very Low Likelihood)
**Symptoms Match:** Everything else works
**Why:** LED ring hardware failure
**How to Check:** Multimeter, try direct power
**How to Fix:** Replace hardware

### 7. Wrong Firmware on Device (Low Likelihood)
**Symptoms Match:** If Dec 12 flash failed
**Why:** Device still has old firmware
**How to Check:** Serial output shows compile date
**How to Fix:** Re-flash with confirmed upload

---

## Documentation Needed

### Create: "LED Behavior Reference Guide"
**Contents:**
- Photos/videos of normal LED patterns
- Description of each state and its LED pattern
- Troubleshooting flowchart for LED issues
- Common LED problems and solutions

### Create: "LED Configuration Guide"
**Contents:**
- Complete explanation of LED config sections
- How to customize LED colors and patterns
- How to control LEDs via Home Assistant
- How to disable/enable LEDs

### Update: "Troubleshooting Guide"
**Add section:**
- LED troubleshooting procedures
- How to test LED functionality
- Serial output interpretation for LED issues

### Create: "Serial Console Guide"
**Contents:**
- How to connect to serial console
- What to expect in serial output
- How to interpret boot messages
- How to identify errors

---

## Next Steps

1. **URGENT:** Connect to serial console and observe boot sequence
   - Confirms firmware is running
   - Shows LED initialization (or failure)
   - Reveals any error messages

2. **HIGH PRIORITY:** Review LED configuration in respeaker.yaml
   - Document current LED settings
   - Check for obvious issues (disabled, wrong pins, etc.)

3. **HIGH PRIORITY:** Check compilation logs
   - Verify LED code compiled successfully
   - Look for any warnings or errors

4. **MEDIUM PRIORITY:** Test LED control via HA (if possible)
   - Requires fixing encryption issue first
   - Or test via temporary no-encryption firmware

5. **MEDIUM PRIORITY:** Document expected LED behavior
   - Create reference guide
   - Video/photos if possible

6. **LOW PRIORITY:** Hardware inspection
   - Only if all software checks pass
   - Last resort before suspecting hardware failure

---

## Related Issues

This LED investigation ties into:
1. **Encryption handshake failure** - May be same root cause
2. **Dec 12 firmware flash status** - Did it complete?
3. **Current firmware version** - What's actually running?
4. **Home Assistant connection** - Needed to test LED control

Solving the encryption issue may also solve the LED issue, or vice versa. They may be symptoms of the same problem (wrong firmware running).

---

*This document should be updated as we answer these questions through investigation.*
*Priority: Start with Phase 1 (serial console) to get actual device state information.*
