# Plan 1 — Clean Restart (Home Assistant + ESPHome + ReSpeaker XVF3800 → VAPI)

This plan restarts the project from zero with a gated, test-first flow. Each phase ends with objective checks so the next step begins from a known-good baseline.

## Target Outcome (Definition of Done)

1. `docker compose up -d` brings up Home Assistant and ESPHome reliably on the Raspberry Pi.
2. The ReSpeaker XVF3800 device:
   - Boots consistently
   - Has a stable identity (name + stable network address strategy)
   - Runs a known firmware build (compilation timestamp visible via logs)
3. Home Assistant shows the ESPHome device as connected and entities are available.
4. A voice interaction can be initiated from the satellite and round-tripped through a VAPI-backed flow (start with text round-trip, then advance to end-to-end audio).
5. A repeatable “rebuild + verify” runbook exists (commands, artifacts, and checkpoints).

## Principles (How We Work This Time)

- **One source of truth:** secrets, device name, and network identity live in one place and are referenced everywhere else.
- **Gated steps:** never “continue” without passing the checks for the current phase.
- **Artifacts by default:** compilation output, upload output, and key configuration snapshots get written to timestamped files.
- **Reproducible commands:** prefer scripted commands (`make`/scripts) over manual copy/paste.
- **Small changes, frequent verification:** keep deltas minimal and validate after each.

## Phase Plan (Start Over From the Beginning)

### Phase 0 — Decide the concrete shape of the end-to-end system

- Confirm the desired end-to-end flow (wake word → capture → process → respond) and which part of the pipeline VAPI owns (text-only vs full audio).
- Define acceptance tests for:
  - Container health (ports, logs)
  - Device health (USB, logs, network presence)
  - Home Assistant ↔ ESPHome connectivity (entities available)
  - Voice loop (first text, then audio)

### Phase 1 — Create a clean-room baseline with rollback

- Take a timestamped backup of the current `config/` and `esphome/` trees.
- Create a fresh “clean” Home Assistant configuration directory (new onboarding state).
- Standardize a project `.env` (or equivalent) with:
  - Pi hostname/IP
  - Device hostname
  - Ports (8123, 6052, 6053)
  - Paths for config + artifacts

### Phase 2 — Bring up Home Assistant + ESPHome in Docker and verify health

- Start the stack with `docker compose up -d`.
- Verify both UIs respond locally and over LAN.
- Create a single “health check” command/script that checks:
  - Containers running
  - HTTP responsiveness on 8123 and 6052
  - Recent logs contain “ready” signals

### Phase 3 — Establish secrets + configuration boundaries

- Make secrets explicit and centralized (WiFi, OTA password, API encryption key).
- Ensure all configs reference secrets via `!secret` (no inline secrets).
- Add a “config validate” command/script for ESPHome.

### Phase 4 — Build firmware in a controlled, repeatable way

- Compile firmware from a clean build context.
- Save:
  - Build output log
  - Firmware artifacts (factory + OTA binaries)
  - A small manifest file (timestamp, git rev if applicable, key config hashes)

### Phase 5 — Flash and verify the device deterministically

- Use a single, repeatable flashing path (USB as default).
- Capture upload output to a timestamped log.
- Immediately after flashing:
  - Collect serial logs from boot
  - Confirm compilation timestamp
  - Confirm network presence (mDNS + ping)

### Phase 6 — Pair the device to Home Assistant with a clean integration state

- Add the ESPHome device to Home Assistant using hostname/IP and the shared encryption key.
- Confirm entities populate and are readable.
- Record the entity IDs needed for later automation/tests (LED, mic, speaker, satellite/assist).

### Phase 7 — Validate “satellite fundamentals” (LED + mic + speaker)

- Validate that basic device controls work (LED brightness/color, playback, mute).
- Validate basic Assist interactions inside Home Assistant (even before VAPI) to prove the audio path.

### Phase 8 — Introduce VAPI in the smallest testable increments

- Start with a **text round-trip**:
  - A small bridge service (or HA custom integration) that can accept text and return text using VAPI.
  - Verified with `curl` and Home Assistant service calls.
- Then evolve to **audio round-trip**:
  - Decide whether audio streams through HA Assist pipeline or a dedicated bridge.
  - Add the minimum glue required and test with a single end-to-end utterance.

### Phase 9 — Operationalize: monitoring, backups, runbooks

- Add “doctor” checks for:
  - Device reachable
  - ESPHome API reachable
  - HA sees device connected
- Add a backup routine for:
  - Current configs
  - Firmware artifacts
  - Any bridge service configs
- Update docs with the final “rebuild from scratch” checklist.

---

## Prompt Pack (Copy/Paste Prompts for a Coding Agent)

Each prompt is self-contained and ends with objective win conditions. Use them one at a time.

### Prompt 1 — Baseline backup + inventory snapshot

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Create a timestamped backup of the current Home Assistant and ESPHome state that is safe to keep locally (no secrets printed to the console).
2) Write a short inventory file describing what’s running and where (paths, ports, container names/images, device identifiers we’re targeting).

Constraints:
- Do not delete or modify existing config yet.
- Do not commit or echo secrets into the terminal output. Redact sensitive values in any generated docs.

Win conditions:
- A new file exists at backups/backup-YYYYMMDD-HHMMSS.tar.gz containing at least config/ and esphome/.
- A new file exists at docs/plan/baseline-YYYYMMDD-HHMMSS.md with: stack ports, container images, paths, and the target device hostname/IP strategy (placeholders ok).
```

### Prompt 2 — Clean-room directories + environment configuration

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Create a clean-room Home Assistant config directory (so we can onboard from scratch without losing the backup).
2) Introduce an .env (or equivalent) that centralizes: PI_HOST, HA_PORT, ESPHOME_PORT, DEVICE_NAME, DEVICE_HOSTNAME, and an ARTIFACTS_DIR.
3) Update docker-compose.yml (or add a docker-compose.override.yml) to use the clean-room config directory without breaking the existing setup.

Constraints:
- Do not place real secrets into git-tracked files; use placeholders and document where to fill them in locally.
- Keep changes minimal and reversible.

Win conditions:
- `docker compose config` exits 0.
- The compose file(s) clearly reference the clean-room config path via a variable or a documented constant.
- A new file exists at .env.example showing required variables (no real secrets).
```

### Prompt 3 — Start the stack + add a health-check script

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Start Home Assistant and ESPHome via docker compose.
2) Add a single script (e.g., scripts/healthcheck.sh) that verifies:
   - both containers are running
   - HA HTTP responds on port 8123
   - ESPHome HTTP responds on port 6052
   - logs show the services are ready

Constraints:
- Keep the healthcheck script fast (<10s) and readable.

Win conditions:
- `docker compose ps` shows `homeassistant` and `esphome` in a running state.
- `curl -fsS http://localhost:8123/` succeeds.
- `curl -fsS http://localhost:6052/` succeeds.
- `scripts/healthcheck.sh` exits 0 when the stack is healthy and non-zero when a container is stopped.
```

### Prompt 4 — Home Assistant onboarding + API token smoke test

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Guide the user through Home Assistant onboarding (UI) and creating a long-lived access token.
2) Add a local-only way to store the token (not committed), and add a script that uses it to call the HA API and prove auth works.

Constraints:
- Do not store the token in any tracked file. Prefer a local `.env` entry or a separate untracked file.

Win conditions:
- Running `scripts/ha_api_smoke_test.sh` prints the JSON from `GET /api/` and exits 0.
- No tracked files contain the token (verify by searching the repo for a token substring placeholder like `Bearer` + user-provided prefix).
```

### Prompt 5 — ESPHome secrets boundary + config validation command

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Ensure ESPHome secrets are centralized and referenced via `!secret` (wifi, ota, api encryption key).
2) Add an `.example` secrets file with placeholders and clear instructions.
3) Add a script that validates `esphome/respeaker.yaml` using the ESPHome Docker image.

Constraints:
- Do not expose real WiFi credentials or encryption keys in tracked files.

Win conditions:
- `esphome/secrets.yaml` is present locally (user-provided) and `esphome/secrets.yaml.example` exists with placeholders.
- `scripts/esphome_validate.sh` exits 0 and prints “Configuration is valid” (or equivalent) for `respeaker.yaml`.
```

### Prompt 6 — Deterministic firmware build + artifact capture

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Add a script that compiles `esphome/respeaker.yaml` in a clean, repeatable way.
2) Save the build log and copy firmware artifacts to an artifacts directory with a timestamped subfolder.
3) Write a small manifest file alongside the artifacts containing build timestamp and the compile-time string, plus hashes of the produced binaries.

Constraints:
- Artifacts should not overwrite previous artifacts.

Win conditions:
- Running `scripts/esphome_build.sh` creates `artifacts/respeaker/BUILD-YYYYMMDD-HHMMSS/` with:
  - a build log file
  - `firmware.bin` and `firmware.factory.bin` (and `firmware.ota.bin` if produced)
  - `manifest.json` (or `.md`) that includes SHA256 hashes for each binary
```

### Prompt 7 — USB flash with captured logs + post-flash verification

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Add a script that uploads the latest compiled firmware to the device over USB (`/dev/ttyACM0`) and captures the full upload output to a timestamped log.
2) Add a second script that captures serial logs after boot (via ESPHome logs) to a timestamped file.
3) Define a post-flash checklist in docs (short) that includes: compilation timestamp from logs, IP/mDNS presence, and basic API readiness.

Constraints:
- Ask the user to confirm before flashing.
- Never assume the device path; verify `/dev/ttyACM0` exists before running upload.

Win conditions:
- `scripts/esphome_upload_usb.sh` refuses to run if `/dev/ttyACM0` is missing.
- After a successful upload, an upload log exists under `artifacts/respeaker/UPLOAD-YYYYMMDD-HHMMSS/`.
- `scripts/esphome_serial_capture.sh` produces a serial log file and includes an “Application compiled on …” line.
```

### Prompt 8 — Pair the device to Home Assistant and verify entity availability

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Guide the user through adding the ESPHome device in Home Assistant (UI) using the device hostname or IP and the shared encryption key.
2) Add a script that queries Home Assistant’s States API and asserts that a small set of key entities exist and are not `unavailable`.
3) Write a short `docs/runbook-device-verification.md` that lists the entity IDs used by the script.

Constraints:
- The script must not hardcode the token; read from a local untracked env var.

Win conditions:
- `scripts/ha_entities_smoke_test.sh` exits 0 and prints the state of at least: one LED-related entity, one mic-related entity, and one speaker/media entity.
- The smoke test fails (non-zero) if any required entity is missing or `unavailable`.
```

### Prompt 9 — Satellite fundamentals smoke test (LED + mic + speaker)

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Add a runbook section that describes how to do three manual checks:
   - LED brightness/color change
   - microphone mute/unmute
   - speaker playback
2) Where possible, add CLI scripts that trigger each action via Home Assistant service calls.

Win conditions:
- A new file exists at `docs/runbook-satellite-smoke-test.md` with exact steps and expected outcomes.
- If service-call scripts are implemented, each script prints a success response from HA and exits 0.
```

### Prompt 10 — Text-first VAPI bridge (local service + curl tests)

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Implement a small local HTTP service (in this repo) that exposes:
   - `GET /healthz` → 200 OK
   - `POST /vapi/text` with `{ "text": "..." }` → `{ "reply": "..." }`
2) Add docker-compose wiring so the service can run alongside HA/ESPHome (host networking is fine).
3) Support a “stub mode” (no external calls) so the system is testable without VAPI credentials.

Constraints:
- Do not require external network access for stub mode tests.
- Keep the service minimal and documented.

Win conditions:
- `curl -fsS http://localhost:<bridge_port>/healthz` succeeds.
- `curl -fsS -X POST http://localhost:<bridge_port>/vapi/text -d '{"text":"ping"}'` returns JSON with a `reply` string in stub mode.
- `docker compose up -d` brings up the bridge service without breaking HA/ESPHome.
```

### Prompt 11 — Wire text bridge into Home Assistant as a conversation backend (minimum viable)

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Configure Home Assistant so a text prompt can be sent to the local bridge and a response returned inside HA (use the smallest HA-native mechanism that works: e.g., `rest_command` + `script`, or a minimal custom integration if needed).
2) Provide a single “text round-trip” test that can be executed from the HA UI and from the CLI.

Constraints:
- Keep credentials and tokens untracked.
- Prefer configuration that is easy to remove/replace later.

Win conditions:
- From HA (UI), a user can trigger a text round-trip and see the bridge’s reply.
- From CLI, `scripts/ha_vapi_text_roundtrip.sh "hello"` prints a non-empty reply and exits 0.
```

### Prompt 12 — End-to-end voice round-trip acceptance test

```text
You are a coding agent working in /home/stewartalsop/prototypes/home-assistant.

Task:
1) Define and document a single end-to-end acceptance test for the voice satellite:
   - trigger (wake word or manual start)
   - speak a short phrase
   - verify the phrase reaches the VAPI-backed flow
   - play back a spoken response
2) Add any minimal configuration or scripts required to make this repeatable.

Constraints:
- Keep this to one “happy path” test.
- Any manual steps must be explicit (what the user does and what output to capture).

Win conditions:
- A new file exists at `docs/acceptance-voice-roundtrip.md` describing the test and the evidence to capture (logs + timestamps).
- Running the test produces:
  - a Home Assistant log excerpt showing the request start and completion
  - a bridge log excerpt showing the request received and replied
  - audible playback on the device (user confirmation)
```

