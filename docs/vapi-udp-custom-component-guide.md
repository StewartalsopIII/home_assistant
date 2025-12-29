# Option A: Custom ESPHome C++ Component for Vapi UDP Bridge

**Status**: Not yet implemented (documentation for future work)
**Purpose**: Direct audio streaming from ESP32 to Vapi bridge via UDP
**Difficulty**: High (requires C++ programming in ESPHome framework)
**Estimated Time**: 4-8 hours for first implementation

---

## Why This Approach?

### Current State (As of 2025-12-29)
- ✅ ESP32 audio works at 16kHz (UDP bandwidth issue solved)
- ✅ Vapi bridge service exists and is functional
- ❌ ESPHome doesn't have built-in UDP client for streaming audio
- ❌ HA LLM integrations prioritize device control over conversation

### What This Would Enable
- Direct ESP32 → Vapi communication (bypassing Home Assistant Assist)
- Use Vapi's conversational AI without HA's limitations
- Full control over audio pipeline and format
- Custom protocol implementation (VAPB or simplified)

---

## Architecture

### Current Flow (HA Assist)
```
ESP32 (wake word)
  → ESPHome voice_assistant component
  → Home Assistant Assist API (WebSocket)
  → HA Conversation Agent (Gemini/OpenAI/etc.)
  → HA TTS
  → ESP32 speaker
```

### Target Flow (Vapi Direct)
```
ESP32 (wake word)
  → Custom UDP Audio Streaming Component
  → Raspberry Pi Vapi Bridge (UDP 9123)
  → Vapi API (WebSocket)
  → Pi Bridge
  → ESP32 speaker (UDP)
```

---

## Implementation Options

### Option 1A: Custom ESPHome Component (Full Implementation)

**Create a new ESPHome component from scratch.**

#### Files to Create
```
esphome/components/vapi_audio_stream/
├── __init__.py           # Component registration
├── vapi_audio_stream.h   # C++ header
├── vapi_audio_stream.cpp # C++ implementation
└── README.md             # Documentation
```

#### Component Responsibilities
1. **Audio Capture**: Interface with `i2s_audio` microphone component
2. **Format Conversion**: 16kHz/32-bit/stereo → 16kHz/16-bit/mono (if needed)
3. **UDP Client**: Send audio packets to bridge IP:port
4. **Protocol**: Implement VAPB protocol or simplified raw PCM
5. **Session Management**: Start/stop streaming on wake word events
6. **Speaker Handling**: Receive UDP packets and play through speaker

#### YAML Configuration
```yaml
external_components:
  - source: components/  # Local components directory
    components: [vapi_audio_stream]

vapi_audio_stream:
  id: vapi_stream
  bridge_host: 192.168.2.65  # Your Pi's IP
  bridge_port: 9123
  session_timeout: 20s

  # Audio settings
  microphone: i2s_mics
  speaker: i2s_audio_speaker

  # Optional: VAPB protocol settings
  use_protocol: true  # false = raw PCM
  magic_bytes: "VAPB"

  # Callbacks
  on_session_start:
    - logger.log: "Vapi session started"
  on_session_end:
    - logger.log: "Vapi session ended"

# Hook into voice_assistant wake word
voice_assistant:
  on_wake_word_detected:
    - vapi_audio_stream.start:
        id: vapi_stream
```

#### C++ Implementation Outline

**vapi_audio_stream.h**:
```cpp
#pragma once

#include "esphome/core/component.h"
#include "esphome/components/microphone/microphone.h"
#include "esphome/components/speaker/speaker.h"
#include <WiFiUdp.h>

namespace esphome {
namespace vapi_audio_stream {

class VapiAudioStream : public Component {
 public:
  void setup() override;
  void loop() override;

  void set_bridge_host(const std::string &host) { bridge_host_ = host; }
  void set_bridge_port(uint16_t port) { bridge_port_ = port; }
  void set_microphone(microphone::Microphone *mic) { mic_ = mic; }
  void set_speaker(speaker::Speaker *spk) { speaker_ = spk; }

  void start_session();
  void stop_session();

 protected:
  std::string bridge_host_;
  uint16_t bridge_port_{9123};
  microphone::Microphone *mic_{nullptr};
  speaker::Speaker *speaker_{nullptr};

  WiFiUDP udp_;
  bool session_active_{false};
  uint32_t session_id_;
  uint32_t sequence_num_{0};

  void send_audio_packet(const uint8_t *data, size_t len);
  void send_control_message(const char *type);
  void receive_speaker_audio();

  // Audio processing
  void downsample_audio(const int32_t *input, int16_t *output, size_t samples);
  void mix_stereo_to_mono(const int32_t *stereo, int32_t *mono, size_t samples);
};

}  // namespace vapi_audio_stream
}  // namespace esphome
```

**vapi_audio_stream.cpp** (key methods):
```cpp
#include "vapi_audio_stream.h"
#include "esphome/core/log.h"

namespace esphome {
namespace vapi_audio_stream {

static const char *TAG = "vapi_audio_stream";

void VapiAudioStream::setup() {
  ESP_LOGCONFIG(TAG, "Setting up Vapi Audio Stream...");
  ESP_LOGCONFIG(TAG, "  Bridge: %s:%d", bridge_host_.c_str(), bridge_port_);

  // Initialize UDP
  udp_.begin(0);  // Bind to any local port

  // Generate session ID (use MAC address or random)
  session_id_ = ESP.getEfuseMac() & 0xFFFFFFFF;
}

void VapiAudioStream::loop() {
  if (!session_active_) return;

  // Read audio from microphone (non-blocking)
  size_t bytes_read = 0;
  uint8_t buffer[480];  // 10ms at 16kHz/16-bit/mono

  if (mic_->read(buffer, sizeof(buffer), &bytes_read) == ESP_OK) {
    if (bytes_read > 0) {
      send_audio_packet(buffer, bytes_read);
    }
  }

  // Check for incoming speaker audio
  receive_speaker_audio();
}

void VapiAudioStream::start_session() {
  ESP_LOGI(TAG, "Starting Vapi session");
  session_active_ = true;
  sequence_num_ = 0;

  // Send CONTROL{type: "start"} message
  send_control_message("start");
}

void VapiAudioStream::stop_session() {
  ESP_LOGI(TAG, "Stopping Vapi session");

  // Send CONTROL{type: "end"} message
  send_control_message("end");

  session_active_ = false;
}

void VapiAudioStream::send_audio_packet(const uint8_t *data, size_t len) {
  // Build VAPB packet header (16 bytes)
  uint8_t packet[508];  // Max UDP payload size for ESP32

  // Magic bytes: "VAPB"
  packet[0] = 'V'; packet[1] = 'A'; packet[2] = 'P'; packet[3] = 'B';

  // Version: 1
  packet[4] = 1;

  // Packet type: MIC_AUDIO = 1
  packet[5] = 1;

  // Session ID (4 bytes, big-endian)
  packet[6] = (session_id_ >> 24) & 0xFF;
  packet[7] = (session_id_ >> 16) & 0xFF;
  packet[8] = (session_id_ >> 8) & 0xFF;
  packet[9] = session_id_ & 0xFF;

  // Sequence number (4 bytes, big-endian)
  packet[10] = (sequence_num_ >> 24) & 0xFF;
  packet[11] = (sequence_num_ >> 16) & 0xFF;
  packet[12] = (sequence_num_ >> 8) & 0xFF;
  packet[13] = sequence_num_ & 0xFF;

  // Reserved (2 bytes)
  packet[14] = 0; packet[15] = 0;

  // Copy audio data (max 480 bytes to fit in 508-byte packet)
  size_t payload_len = std::min(len, (size_t)480);
  memcpy(packet + 16, data, payload_len);

  // Send UDP packet
  udp_.beginPacket(bridge_host_.c_str(), bridge_port_);
  udp_.write(packet, 16 + payload_len);
  udp_.endPacket();

  sequence_num_++;
}

void VapiAudioStream::send_control_message(const char *type) {
  // Build CONTROL packet with JSON payload
  char json_buffer[256];
  snprintf(json_buffer, sizeof(json_buffer),
           "{\"type\":\"%s\",\"mic\":{\"sample_rate\":16000,\"bits\":16,\"channels\":1}}",
           type);

  // Build VAPB header for CONTROL packet (type = 3)
  uint8_t packet[508];
  memcpy(packet, "VAPB", 4);
  packet[4] = 1;  // Version
  packet[5] = 3;  // CONTROL packet type

  // Session ID
  packet[6] = (session_id_ >> 24) & 0xFF;
  packet[7] = (session_id_ >> 16) & 0xFF;
  packet[8] = (session_id_ >> 8) & 0xFF;
  packet[9] = session_id_ & 0xFF;

  // Sequence (not used for CONTROL)
  packet[10] = packet[11] = packet[12] = packet[13] = 0;
  packet[14] = packet[15] = 0;

  // Copy JSON
  size_t json_len = strlen(json_buffer);
  memcpy(packet + 16, json_buffer, json_len);

  udp_.beginPacket(bridge_host_.c_str(), bridge_port_);
  udp_.write(packet, 16 + json_len);
  udp_.endPacket();
}

void VapiAudioStream::receive_speaker_audio() {
  int packet_size = udp_.parsePacket();
  if (packet_size == 0) return;

  uint8_t buffer[508];
  int len = udp_.read(buffer, sizeof(buffer));

  // Verify VAPB magic bytes
  if (len < 16 || memcmp(buffer, "VAPB", 4) != 0) {
    ESP_LOGW(TAG, "Invalid packet received");
    return;
  }

  uint8_t packet_type = buffer[5];

  if (packet_type == 2) {  // SPK_AUDIO
    // Extract audio payload (skip 16-byte header)
    uint8_t *audio_data = buffer + 16;
    size_t audio_len = len - 16;

    // Write to speaker
    if (speaker_ != nullptr) {
      speaker_->play(audio_data, audio_len);
    }
  }
}

void VapiAudioStream::downsample_audio(const int32_t *input, int16_t *output, size_t samples) {
  // Simple decimation: keep every 3rd sample (48kHz → 16kHz)
  // Only needed if mic is still at 48kHz
  for (size_t i = 0, j = 0; i < samples; i += 3, j++) {
    output[j] = (int16_t)(input[i] >> 16);  // Convert 32-bit → 16-bit
  }
}

void VapiAudioStream::mix_stereo_to_mono(const int32_t *stereo, int32_t *mono, size_t samples) {
  // Average left and right channels
  for (size_t i = 0, j = 0; i < samples; i += 2, j++) {
    int64_t mixed = ((int64_t)stereo[i] + (int64_t)stereo[i+1]) / 2;
    mono[j] = (int32_t)mixed;
  }
}

}  // namespace vapi_audio_stream
}  // namespace esphome
```

**\_\_init\_\_.py**:
```python
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import microphone, speaker
from esphome.const import CONF_ID

DEPENDENCIES = ['wifi', 'microphone', 'speaker']

vapi_audio_stream_ns = cg.esphome_ns.namespace('vapi_audio_stream')
VapiAudioStream = vapi_audio_stream_ns.class_('VapiAudioStream', cg.Component)

CONF_BRIDGE_HOST = 'bridge_host'
CONF_BRIDGE_PORT = 'bridge_port'
CONF_MICROPHONE = 'microphone'
CONF_SPEAKER = 'speaker'

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(VapiAudioStream),
    cv.Required(CONF_BRIDGE_HOST): cv.string,
    cv.Optional(CONF_BRIDGE_PORT, default=9123): cv.port,
    cv.Required(CONF_MICROPHONE): cv.use_id(microphone.Microphone),
    cv.Required(CONF_SPEAKER): cv.use_id(speaker.Speaker),
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add(var.set_bridge_host(config[CONF_BRIDGE_HOST]))
    cg.add(var.set_bridge_port(config[CONF_BRIDGE_PORT]))

    mic = await cg.get_variable(config[CONF_MICROPHONE])
    cg.add(var.set_microphone(mic))

    spk = await cg.get_variable(config[CONF_SPEAKER])
    cg.add(var.set_speaker(spk))
```

---

### Option 1B: Simplified Approach (Raw PCM, No Protocol)

**If the VAPB protocol proves too complex, simplify:**

1. **Remove protocol overhead**: Send raw PCM audio bytes directly
2. **Modify bridge to accept raw PCM**: Update `bridge.py` to parse raw audio instead of VAPB
3. **Simpler implementation**: ~50% less code

**Trade-offs**:
- Lose session management features
- Harder to debug (no packet headers)
- No sequence numbers (can't detect packet loss)

---

### Option 2: Lambda-Based UDP Streaming (Quick Hack)

**Use ESPHome's lambda capabilities for a proof-of-concept.**

#### Challenges
- ESPHome's `voice_assistant` component doesn't expose raw audio in `on_start`
- Would need to hook into internal microphone buffer (not officially supported)
- Fragile and likely to break with ESPHome updates

#### Example (Pseudocode)
```yaml
voice_assistant:
  on_start:
    - lambda: |-
        // WARNING: This accesses internal APIs and may break
        auto mic = id(i2s_mics);

        // Hypothetical audio capture (not real API)
        uint8_t buffer[480];
        size_t bytes_read = mic->read(buffer, sizeof(buffer));

        // Send via UDP
        WiFiUDP udp;
        udp.beginPacket("192.168.2.65", 9123);
        udp.write(buffer, bytes_read);
        udp.endPacket();
```

**Not recommended**: Use Option 1A for production.

---

## Prerequisites

### Skills Required
- C++ programming
- ESPHome component development
- Understanding of I2S audio
- UDP socket programming
- Debugging with serial logs

### Development Environment
1. **ESPHome development setup**:
   ```bash
   pip install esphome
   ```

2. **Local component development**:
   - Create `esphome/components/` directory in your repo
   - ESPHome will automatically load local components

3. **Testing**:
   - Use `esphome logs` to monitor serial output
   - Wireshark or `tcpdump` to verify UDP packets

### Bridge Service Must Be Running
```bash
# Start Vapi bridge (from repo root)
/home/stewartalsop/prototypes/home-assistant/vapi_bridge/.venv/bin/python -m vapi_bridge.main

# Or as systemd service
sudo systemctl start vapi-bridge
```

---

## Testing Strategy

### Phase 1: Component Setup
1. Compile with component (should build without errors)
2. Flash to ESP32
3. Check logs for "Setting up Vapi Audio Stream..."
4. Verify UDP socket initializes

### Phase 2: Wake Word Integration
1. Trigger wake word ("Okay Nabu")
2. Check logs for "Starting Vapi session"
3. Use tcpdump to verify UDP packets sent to Pi

### Phase 3: Bridge Reception
1. Monitor bridge logs for received packets
2. Verify VAPB packet parsing works
3. Check session ID matches

### Phase 4: Vapi Connection
1. Verify bridge creates Vapi WebSocket
2. Check Vapi receives audio
3. Monitor for response audio

### Phase 5: Speaker Playback
1. Verify UDP packets received from bridge
2. Check speaker plays audio
3. Test end-to-end latency

---

## Debugging Tools

### ESP32 Side
```bash
# Monitor serial logs
esphome logs esphome/respeaker.yaml --device /dev/ttyUSB0

# Or via network
esphome logs esphome/respeaker.yaml --device respeaker-xvf3800-assistant.local
```

### Network Side
```bash
# Capture UDP traffic
sudo tcpdump -i wlan0 udp port 9123 -X

# Count packets
sudo tcpdump -i wlan0 udp port 9123 -c 100

# Save to file
sudo tcpdump -i wlan0 udp port 9123 -w vapi-udp.pcap
```

### Bridge Side
```bash
# Bridge logs
tail -f /tmp/vapi-bridge.log

# Or if using systemd
journalctl -u vapi-bridge -f
```

---

## Expected Challenges

### 1. Audio Format Mismatch
**Problem**: Bridge expects different format than ESP32 sends
**Solution**: Add logging to both sides showing exact format received

### 2. UDP Packet Loss
**Problem**: WiFi interference causes dropped packets
**Solution**: Implement sequence number tracking and logging

### 3. Speaker Buffer Management
**Problem**: Audio playback stutters or has gaps
**Solution**: Implement ring buffer with proper flow control

### 4. Session Lifecycle
**Problem**: Session doesn't end properly after idle timeout
**Solution**: Implement timer-based session management on ESP32 side

### 5. Memory Constraints
**Problem**: ESP32 runs out of heap memory
**Solution**: Reduce buffer sizes, use static allocation where possible

---

## Estimated Effort

| Task | Time | Difficulty |
|------|------|-----------|
| Setup development environment | 30 min | Easy |
| Component skeleton code | 1 hour | Medium |
| UDP packet sending | 1 hour | Medium |
| VAPB protocol implementation | 1-2 hours | Medium |
| Audio capture integration | 2 hours | Hard |
| Speaker playback integration | 1-2 hours | Medium |
| Testing and debugging | 2-4 hours | Hard |
| **Total** | **8-12 hours** | **Medium-Hard** |

---

## When to Consider This Approach

### Do This If:
- ✅ You need Vapi's specific AI capabilities (personality, tools, etc.)
- ✅ HA LLM integrations don't meet your conversation needs
- ✅ You're comfortable with C++ and ESPHome internals
- ✅ You have time for debugging and iteration

### Don't Do This If:
- ❌ HA LLM integrations work fine for you (Option C with dual agents)
- ❌ You're not comfortable with C++ programming
- ❌ You need it working this week (use existing HA integrations)
- ❌ The learning curve seems too steep

---

## Future Improvements

Once basic implementation works:

1. **Error handling**: Retry logic, timeout handling
2. **Quality optimization**: Better resampling, noise reduction
3. **Metrics**: Latency measurement, packet loss tracking
4. **Multiple bridges**: Load balancing across multiple Pi devices
5. **Compression**: Implement Opus codec for bandwidth reduction
6. **Wake word pass-through**: Let Vapi handle wake word detection

---

## Resources

### ESPHome Component Development
- [ESPHome Custom Components](https://esphome.io/custom/custom_component.html)
- [ESPHome I2S Audio](https://esphome.io/components/i2s_audio.html)
- [ESPHome Microphone](https://esphome.io/components/microphone/)
- [ESPHome Speaker](https://esphome.io/components/speaker/)

### UDP Programming
- [Arduino WiFiUDP Reference](https://www.arduino.cc/reference/en/libraries/wifi/wifiudp/)
- [ESP32 UDP Examples](https://github.com/espressif/arduino-esp32/tree/master/libraries/WiFi/examples/WiFiUDPClient)

### Vapi Bridge
- Local implementation: `/home/stewartalsop/prototypes/home-assistant/vapi_bridge/`
- Protocol: `vapi_bridge/protocol.py`
- Bridge logic: `vapi_bridge/bridge.py`

---

## Conclusion

This approach requires significant C++ development but provides:
- ✅ Complete control over audio pipeline
- ✅ Direct Vapi integration (no HA limitations)
- ✅ Custom protocol implementation
- ✅ Learning opportunity for ESPHome internals

**Current recommendation**: Start with HA LLM integrations (Option C with dual agents), then implement this if conversation quality isn't sufficient.

**Status**: All groundwork is complete:
- ✅ Audio works at 16kHz (bandwidth issue solved)
- ✅ Vapi bridge service ready and tested
- ✅ Architecture designed
- ⏳ Waiting for C++ component implementation

**When you're ready to implement this, you have a complete roadmap here.**
