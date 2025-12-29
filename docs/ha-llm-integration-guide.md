# Home Assistant LLM Integration Guide (2025)

**Last Updated**: December 29, 2025
**Status**: Researched and tested with Google Gemini, applicable to all LLM integrations

## Table of Contents
1. [The Promise vs. Reality](#the-promise-vs-reality)
2. [The Critical Limitation](#the-critical-limitation)
3. [Available LLM Integrations](#available-llm-integrations)
4. [Configuration Guide](#configuration-guide)
5. [Workarounds for General Conversation](#workarounds-for-general-conversation)
6. [Troubleshooting](#troubleshooting)
7. [Recommendations](#recommendations)

---

## The Promise vs. Reality

### What the Documentation Suggests
Home Assistant (2024.6+) allows you to integrate LLMs like OpenAI, Google Gemini, and Anthropic Claude as conversation agents for your voice assistants. The marketing implies you can have natural conversations with AI through your ESPHome satellites.

### What Actually Happens
**When you enable device control (the "Assist" checkbox), the LLM prioritizes interpreting everything as a device control command rather than engaging in general conversation.**

### Example
- **You say**: "Tell me a joke"
- **Expected**: AI tells you a joke
- **Actual (with Assist enabled)**: "I couldn't find a device called 'joke'"

---

## The Critical Limitation

### The "Control Home Assistant" Checkbox

All LLM integrations have a **"Control Home Assistant"** setting (specifically the "Assist" checkbox) that fundamentally changes behavior:

| Setting | Device Control | General Conversation |
|---------|---------------|---------------------|
| **Assist ENABLED** | ✅ Works | ❌ Limited/broken |
| **Assist DISABLED** | ❌ No control | ✅ Works naturally |

### Why This Happens

When "Assist" is enabled, the LLM receives access to Home Assistant's Assist API, which includes:
- List of all devices and entities
- Available services and actions
- Intent system for device control

The LLM's system prompt becomes focused on device control, causing it to interpret queries through that lens rather than treating them as general conversation.

### This Affects ALL LLM Integrations
- OpenAI/ChatGPT ✓
- Google Gemini ✓
- Anthropic Claude ✓
- Ollama (local) ✓

**This is a design choice, not a bug**, but it's poorly documented.

---

## Available LLM Integrations

### Official Integrations (Built into Home Assistant)

#### 1. OpenAI / ChatGPT
- **Integration**: `openai_conversation`
- **Models**: GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Best for**: Non-smart-home questions (better than Gemini for general knowledge)
- **Cost**: ~$0.50-1.00 per 1M tokens (14x more expensive than Gemini)
- **Setup**: Settings → Devices & Services → Add Integration → OpenAI

#### 2. Google Gemini
- **Integration**: `google_generative_ai_conversation`
- **Models**: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
- **Best for**: Cost-effective smart home control
- **Cost**: ~$0.035-0.075 per 1M tokens (14x cheaper than OpenAI)
- **Setup**: Settings → Devices & Services → Add Integration → Google Generative AI
- **Note**: TTS available via gemini-2.0-flash-tts

#### 3. Anthropic Claude
- **Integration**: `anthropic`
- **Models**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Best for**: Extended thinking, web search integration
- **Features**: Supports custom instructions via templating
- **Setup**: Settings → Devices & Services → Add Integration → Anthropic
- **Limitation**: Does not integrate with sentence triggers

#### 4. Ollama (Local LLMs)
- **Integration**: `ollama`
- **Models**: Any Ollama model (llama3.2, mistral, deepseek, etc.)
- **Best for**: Privacy, no internet required, zero API costs
- **Requirements**: External Ollama server (separate machine or Docker)
- **Recommended**: llama3.2 for voice (reasoning models too verbose)
- **Setup**: Install Ollama → Pull models → Add integration

### Voice Pipeline Components

Complete voice assistant pipeline requires:
1. **Speech-to-Text (STT)**: Whisper (local), Google AI STT, HA Cloud
2. **Conversation Agent**: Your chosen LLM
3. **Text-to-Speech (TTS)**: Piper (local), Google AI TTS, HA Cloud

---

## Configuration Guide

### Basic Setup (Single Agent)

#### Step 1: Add LLM Integration
1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for: **OpenAI** / **Google Generative AI** / **Anthropic** / **Ollama**
4. Enter API key (or server URL for Ollama)
5. Click **Submit**

#### Step 2: Configure LLM Settings
1. Click **Configure** (gear icon) next to your LLM integration
2. Select model (e.g., gemini-2.0-flash, gpt-4o-mini)
3. **CRITICAL**: Under "Control Home Assistant":
   - ☑️ **Check "Assist"** if you want device control (limits conversation)
   - ☐ **Uncheck "Assist"** if you want general conversation (no device control)
4. (Optional) Add custom instructions/prompt template
5. (Optional) Adjust temperature (higher = more creative)

#### Step 3: Create Voice Assistant
1. Go to **Settings → Voice Assistants**
2. Click **Add Assistant**
3. Name it (e.g., "Gemini Assistant")
4. Select:
   - **Speech-to-Text**: Whisper or Google AI STT
   - **Conversation Agent**: Your LLM (e.g., Google AI Conversation)
   - **Text-to-Speech**: Piper or Google AI TTS
5. Click **Create**

#### Step 4: Assign to Your ESP32 Device
1. Go to **Settings → Devices & Services → ESPHome**
2. Click on your device (e.g., "Respeaker XVF3800 Satellite")
3. Under **Configuration**, click the **Assistant** dropdown
4. Select your newly created assistant
5. Test: Say wake word → Ask a question

---

## Workarounds for General Conversation

### Option 1: Dual Agent Setup (Recommended)

Create **TWO separate LLM agents** to handle different query types:

#### Agent 1: Device Control
```
Settings → Devices & Services → Add Integration → Google Generative AI
├─ Name: "Gemini Control"
├─ Model: gemini-2.0-flash
└─ Control Home Assistant: ✅ Assist ENABLED
```

#### Agent 2: General Conversation
```
Settings → Devices & Services → Add Integration → Google Generative AI
├─ Name: "Gemini Chat"
├─ Model: gemini-2.0-flash
├─ Control Home Assistant: ☐ Assist DISABLED
└─ Custom Instructions: "You are a helpful, friendly AI assistant. Answer questions naturally and conversationally."
```

#### Create Two Voice Assistants
```
Voice Assistant 1: "Smart Home"
├─ STT: Whisper
├─ Agent: Gemini Control
└─ TTS: Piper

Voice Assistant 2: "Chat"
├─ STT: Whisper
├─ Agent: Gemini Chat
└─ TTS: Piper
```

#### Usage
- Switch between assistants on your ESP32 device dropdown
- Use "Smart Home" for device commands
- Use "Chat" for general questions

### Option 2: "Prefer Handling Commands Locally" (Built-in, HA 2024.12+)

**Simpler but has bugs/limitations.**

#### Setup
1. Keep LLM integration with "Assist" **DISABLED**
2. In Voice Assistant configuration, enable:
   - ☑️ **"Prefer handling commands locally"**

#### How It Works
- Device control commands ("turn on kitchen light") → Handled by local Assist (fast, free)
- General questions ("what's the weather?") → Sent to LLM
- Ambiguous queries ("it's dark in the kitchen") → Sent to LLM

#### Known Issues (Community Reports)
- Doesn't fallback to local intents during continued conversations
- Can increase latency from 2.5s to 52s in some cases
- Mixed results with custom sentences

### Option 3: Custom Integrations

#### Fallback Conversation Agent (HACS)
- Routes device control to built-in HA agent
- Routes other queries to LLM
- Single voice assistant with intelligent routing
- Install: HACS → Search "Fallback Conversation Agent"

#### Voice Flow (HACS, November 2024)
- Allows multiple conversation agents in one pipeline
- Routes based on query type
- Install: HACS → Search "Voice Flow"

#### Extended OpenAI Conversation (HACS)
- Multi-agent dispatcher system
- Create specialized agents for different domains
- Complex but highly flexible
- Install: HACS → Search "Extended OpenAI Conversation"

---

## Troubleshooting

### Problem: LLM Only Does Device Control, Not Conversation

**Cause**: "Control Home Assistant" → "Assist" is ENABLED

**Fix**:
1. Settings → Devices & Services → [Your LLM Integration]
2. Click **Configure**
3. Under "Control Home Assistant", **UNCHECK "Assist"**
4. Save and test

### Problem: LLM Responds "Unable to generate response"

**Common causes**:
1. **API quota exceeded** (check your LLM provider dashboard)
2. **Invalid API key** (regenerate and update in HA)
3. **Model deprecation** (switch to supported model)
4. **Function calling errors** with newer Gemini models (try gemini-2.0-flash)

**Fix**:
- Check Home Assistant logs: Settings → System → Logs
- Look for errors from your LLM integration
- Verify API key is valid and has credits

### Problem: Device Commands Work But Responses Are Slow

**Cause**: Every command sent to LLM for interpretation (unnecessary overhead)

**Fix**: Use "Prefer handling commands locally" option to route simple commands directly to Assist

### Problem: LLM Gives Wrong Actions or Loops Messages

**Cause**: Model trying to use unsupported function calling features

**Fix**:
- Switch to recommended model for your LLM
- For Gemini: Use gemini-2.0-flash (not older flash versions)
- For OpenAI: Use gpt-4o-mini or gpt-4o

### Problem: Continued Conversation Doesn't Work

**Cause**: Multi-turn conversation feature requires specific setup

**Fix**:
1. Ensure "Assist" is enabled (needed for continued conversation)
2. Check that voice assistant is configured for conversational mode
3. Note: This feature works better with Assist enabled but limits general conversation

---

## Recommendations

### Best Setup for Most Users (2025)

**Use the Dual Agent approach:**

1. **Create Gemini Chat agent** (Assist DISABLED):
   - Use for: General questions, facts, jokes, weather
   - Fast responses, natural conversation
   - No device control

2. **Create Gemini Control agent** (Assist ENABLED):
   - Use for: Device commands only
   - "Turn on lights", "Set temperature", etc.

3. **Create two voice assistants** pointing to each agent

4. **Assign "Gemini Chat" as default** on your ESP32 devices

5. **Switch to "Gemini Control"** when you need device control for a session

### Cost Optimization

- **Google Gemini**: Best value (14x cheaper than OpenAI, similar quality for smart home)
- **Ollama**: Zero cost if you can run locally (needs separate hardware)
- **OpenAI**: Best for complex reasoning and non-smart-home questions (but expensive)

### Performance Optimization

- Use **Whisper (local)** for STT to avoid cloud latency
- Use **Piper (local)** for TTS for instant responses
- Use **"Prefer handling commands locally"** if you primarily issue device commands

### Privacy

- **Ollama** with local STT/TTS = 100% local, zero cloud
- **OpenAI/Gemini** = All queries sent to cloud (consider data implications)
- **Home Assistant Cloud** = Queries processed by Nabu Casa

---

## Key Learnings

### What We Learned the Hard Way

1. **LLM integrations are primarily designed for device control**, not general conversation. This isn't obvious from the documentation.

2. **Enabling "Assist" fundamentally changes AI behavior**. There's no hybrid mode that works reliably out of the box.

3. **"Prefer handling commands locally" was supposed to solve this** but has mixed results and known bugs (December 2024).

4. **The dual agent setup is the most reliable workaround** but requires manual switching or automation.

5. **OpenAI handles general questions better than Gemini**, but Gemini is 14x cheaper for equivalent smart home control.

6. **All LLM integrations share the same limitation** - it's not specific to Gemini.

### What Actually Works

✅ **Single-purpose agents**: One for device control, one for conversation
✅ **Google Gemini for cost**: Best price/performance for smart home
✅ **Local processing**: Whisper + Piper + Ollama = fast and private
✅ **Custom integrations**: Fallback Conversation Agent, Voice Flow
❌ **Single agent for both**: Doesn't work reliably with current HA architecture

---

## Resources

### Official Documentation
- [Google Gemini Integration](https://www.home-assistant.io/integrations/google_generative_ai_conversation/)
- [OpenAI Integration](https://www.home-assistant.io/integrations/openai_conversation/)
- [Anthropic Integration](https://www.home-assistant.io/integrations/anthropic)
- [Ollama Integration](https://www.home-assistant.io/integrations/ollama/)
- [Voice Assistants Guide](https://www.home-assistant.io/voice_control/)
- [Create AI Personality](https://www.home-assistant.io/voice_control/assist_create_open_ai_personality/)

### Community Guides
- [Fallback Conversation Agent](https://community.home-assistant.io/t/custom-component-fallback-conversation-agent/688936)
- [Voice Flow Integration](https://community.home-assistant.io/t/voice-flow/796467)
- [Multi-Agent Setup](https://community.home-assistant.io/t/multi-agents-in-home-assistant/755529)
- [Local LLM with Ollama](https://peyanski.com/local-ai-with-home-assistant-and-ollama/)

### GitHub Projects
- [Extended OpenAI Conversation](https://github.com/jekalmin/extended_openai_conversation)
- [home-llm (Fine-tuned Local Models)](https://github.com/acon96/home-llm)

---

## Version History

- **2025-12-29**: Initial guide created based on research and testing with Google Gemini
- **Future**: Will update as Home Assistant improves hybrid conversation+control capabilities

---

**Bottom Line**: LLM integration in Home Assistant works, but requires understanding the trade-offs and using workarounds for general conversation. The dual agent setup is currently the most reliable approach for getting both device control and natural conversation.
