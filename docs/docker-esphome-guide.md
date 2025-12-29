# Docker + ESPHome Usage Guide

**Last Updated**: December 29, 2025
**Environment**: Raspberry Pi 4+ running Home Assistant + ESPHome in Docker

---

## Table of Contents
1. [Understanding the Setup](#understanding-the-setup)
2. [Key Concepts](#key-concepts)
3. [Common Commands](#common-commands)
4. [File Paths and Volumes](#file-paths-and-volumes)
5. [Networking](#networking)
6. [Troubleshooting](#troubleshooting)
7. [Pro Tips](#pro-tips)

---

## Understanding the Setup

### What's Running
Your Home Assistant setup uses **Docker containers** for both Home Assistant and ESPHome:

```yaml
# docker-compose.yml
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    network_mode: host

  esphome:
    container_name: esphome
    image: ghcr.io/esphome/esphome
    network_mode: host
```

### Why Docker?
✅ **Consistent environment** - No dependency conflicts
✅ **Easy updates** - `docker pull` to get latest version
✅ **Isolation** - Doesn't pollute your system
✅ **Portability** - Same setup works on any Docker host

### The Trade-off
⚠️ Need to use `docker exec` for commands
⚠️ File paths are different inside containers
⚠️ Slightly more memory usage

---

## Key Concepts

### 1. Commands Must Run Inside Containers

**❌ Won't Work (esphome not installed directly)**:
```bash
esphome run esphome/respeaker.yaml
```

**✅ Works (runs inside Docker container)**:
```bash
docker exec esphome esphome run /config/respeaker.yaml
```

**Anatomy of the command**:
```
docker exec esphome esphome run /config/respeaker.yaml
│         │       │         │    └─ Container path
│         │       │         └────── ESPHome command
│         │       └──────────────── ESPHome program
│         └──────────────────────── Container name
└────────────────────────────────── Docker command
```

### 2. File Paths Are Mapped

**Your host** vs **inside container**:

| Location | Host (Your Pi) | Container | Why |
|----------|---------------|-----------|-----|
| **ESPHome configs** | `./esphome/` | `/config/` | Volume mount |
| **YAML files** | `./esphome/respeaker.yaml` | `/config/respeaker.yaml` | Same file, different path |
| **Home Assistant** | `./config/` | `/config/` | Volume mount |

**Defined in docker-compose.yml**:
```yaml
esphome:
  volumes:
    - ./esphome:/config  # Host path : Container path
```

**What this means**:
- Edit files on your Pi in `./esphome/`
- Container automatically sees them in `/config/`
- Changes sync in real-time (no container restart needed)

### 3. Network Mode: Host

```yaml
esphome:
  network_mode: host
```

**What this means**:
- Container uses the **same network** as your Pi
- Can access devices on local network directly
- No port mapping needed
- ESP32 at `192.168.2.28` is accessible from container

---

## Common Commands

### ESPHome Operations

#### Compile Firmware
```bash
docker exec esphome esphome compile /config/respeaker.yaml
```
**When to use**: Check for errors before uploading

#### Upload Firmware (OTA)
```bash
# Using hostname (recommended)
docker exec esphome esphome upload /config/respeaker.yaml --device respeaker-xvf3800-assistant.local

# Using IP address
docker exec esphome esphome upload /config/respeaker.yaml --device 192.168.2.28
```
**When to use**: Upload to ESP32 over WiFi

#### Run (Compile + Upload)
```bash
docker exec esphome esphome run /config/respeaker.yaml
```
**When to use**: Quick compile and upload in one command

#### View Logs
```bash
# Via network (using hostname)
docker exec esphome esphome logs /config/respeaker.yaml --device respeaker-xvf3800-assistant.local

# Via USB (if connected)
docker exec esphome esphome logs /config/respeaker.yaml --device /dev/ttyUSB0
```
**When to use**: Debug issues, see real-time output

#### Validate Configuration
```bash
docker exec esphome esphome config /config/respeaker.yaml
```
**When to use**: Check YAML syntax before compiling

### Docker Container Management

#### Check Running Containers
```bash
docker ps

# Filter for ESPHome
docker ps | grep esphome
```
**Output**:
```
CONTAINER ID   IMAGE                       STATUS                 PORTS
27d9fffcb8e1   ghcr.io/esphome/esphome     Up 2 weeks (healthy)
```

#### Restart ESPHome Container
```bash
docker restart esphome
```
**When to use**: After configuration changes, if container is unresponsive

#### View Container Logs
```bash
docker logs esphome

# Follow logs in real-time
docker logs -f esphome --tail 50
```

#### Stop/Start Container
```bash
# Stop
docker stop esphome

# Start
docker start esphome
```

#### Access Container Shell
```bash
docker exec -it esphome /bin/bash
```
**When to use**: Debug internal container issues

### File Operations

#### Edit Files on Host (Recommended)
```bash
# Edit on your Pi - changes sync automatically
nano esphome/respeaker.yaml
```
**Why**: Easier, changes persist, no container knowledge needed

#### View Files Inside Container
```bash
docker exec esphome ls -la /config/
```

#### Check ESPHome Version
```bash
docker exec esphome esphome version
```

---

## File Paths and Volumes

### Volume Mounts Explained

**From docker-compose.yml**:
```yaml
esphome:
  volumes:
    - ./esphome:/config  # ESPHome configs
    - /etc/localtime:/etc/localtime:ro  # System time (read-only)
```

### Path Conversion Table

| You Edit Here | Container Sees | ESPHome Command Uses |
|--------------|----------------|---------------------|
| `esphome/respeaker.yaml` | `/config/respeaker.yaml` | `/config/respeaker.yaml` |
| `esphome/secrets.yaml` | `/config/secrets.yaml` | `/config/secrets.yaml` |
| `esphome/.esphome/` | `/config/.esphome/` | `/config/.esphome/` (build cache) |

### Best Practices

✅ **DO**: Edit files in `esphome/` on your Pi
✅ **DO**: Use container paths (`/config/`) in docker exec commands
❌ **DON'T**: Edit files inside container (changes may be lost)
❌ **DON'T**: Mix host and container paths in same command

---

## Networking

### Finding ESP32 Devices

#### Using mDNS (Recommended)
```bash
# ESPHome advertises via mDNS
avahi-browse -rt _esphomelib._tcp

# Should show: respeaker-xvf3800-assistant
```

#### Using Hostname
```bash
# Always use .local suffix
ping respeaker-xvf3800-assistant.local

# Upload using hostname
docker exec esphome esphome upload /config/respeaker.yaml --device respeaker-xvf3800-assistant.local
```

**Benefits**:
- Works even if IP changes
- Easier to remember
- More reliable

#### Finding IP Address
```bash
# From mDNS
avahi-resolve -n respeaker-xvf3800-assistant.local

# From ARP table
arp -n | grep -i "9c:13:9e"  # MAC address prefix

# From Home Assistant
# Settings → Devices & Services → ESPHome → Your device
```

### Network Troubleshooting

#### Check if Device is Reachable
```bash
# Ping test
ping -c 3 respeaker-xvf3800-assistant.local

# Check if OTA port is open
nc -zv 192.168.2.28 3232
```

#### Monitor UDP Traffic (For Debugging)
```bash
# Watch UDP packets on port 9123 (Vapi bridge)
sudo tcpdump -i wlan0 udp port 9123 -n

# Count packets
sudo tcpdump -i wlan0 udp port 9123 -c 100
```

---

## Troubleshooting

### Problem: "esphome: command not found"

**Cause**: Trying to run `esphome` directly on host

**Fix**: Use `docker exec esphome esphome ...`

---

### Problem: "No such file or directory: esphome/respeaker.yaml"

**Cause**: Using host path in docker exec command

**Fix**: Use container path `/config/respeaker.yaml`
```bash
# ❌ Wrong
docker exec esphome esphome run esphome/respeaker.yaml

# ✅ Right
docker exec esphome esphome run /config/respeaker.yaml
```

---

### Problem: OTA Upload Fails "No route to host"

**Possible causes**:
1. ESP32 is offline/crashed
2. IP address changed
3. Device still booting
4. Firewall blocking port 3232

**Fix**:
```bash
# 1. Check if device is online
ping respeaker-xvf3800-assistant.local

# 2. Find current IP
avahi-resolve -n respeaker-xvf3800-assistant.local

# 3. Try hostname instead of IP
docker exec esphome esphome upload /config/respeaker.yaml --device respeaker-xvf3800-assistant.local

# 4. Check if OTA port is reachable
nc -zv 192.168.2.28 3232
```

---

### Problem: Changes to YAML Don't Take Effect

**Cause**: Container might be using cached build

**Fix**:
```bash
# Clean build cache
docker exec esphome esphome clean /config/respeaker.yaml

# Then compile again
docker exec esphome esphome compile /config/respeaker.yaml
```

---

### Problem: USB Device Not Accessible

**Cause**: Container needs device access

**Fix**: Container must be privileged (already configured in your docker-compose.yml)
```yaml
esphome:
  privileged: true  # ✅ Already enabled
```

**Find USB device**:
```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

**Upload via USB**:
```bash
docker exec esphome esphome run /config/respeaker.yaml --device /dev/ttyUSB0
```

---

### Problem: Container Won't Start

**Check logs**:
```bash
docker logs esphome

# Common issues:
# - Port conflict (another container using same port)
# - Volume mount path doesn't exist
# - Configuration error in docker-compose.yml
```

**Restart Docker**:
```bash
sudo systemctl restart docker
docker-compose up -d
```

---

## Pro Tips

### 1. Create a Bash Alias

**Add to ~/.bashrc or ~/.bash_aliases**:
```bash
alias esphome='docker exec esphome esphome'
```

**Reload**:
```bash
source ~/.bashrc
```

**Now you can use**:
```bash
esphome upload /config/respeaker.yaml --device respeaker-xvf3800-assistant.local
```

### 2. Use ESPHome Dashboard (Web UI)

**Already running at**: `http://192.168.2.65:6052/`

**Features**:
- Compile and upload via web interface
- View logs in real-time
- Edit YAML files
- See all devices at a glance
- No command-line needed

**Benefits**:
- Easier for non-technical users
- Visual feedback
- No need to remember container paths

### 3. Quick Log Monitoring

**Watch logs while testing**:
```bash
docker exec esphome esphome logs /config/respeaker.yaml | grep -E "ERROR|WARN|sendto"
```

**Save logs to file**:
```bash
docker exec esphome esphome logs /config/respeaker.yaml > esp32-logs.txt
```

### 4. Multiple ESP32 Devices

**Organize with separate YAML files**:
```
esphome/
├── respeaker.yaml          # Living room device
├── bedroom-satellite.yaml  # Bedroom device
├── kitchen-satellite.yaml  # Kitchen device
└── secrets.yaml            # Shared secrets
```

**Compile all at once**:
```bash
for yaml in /config/*.yaml; do
  docker exec esphome esphome compile "$yaml"
done
```

### 5. Use Hostnames Everywhere

**Configure static hostname in ESPHome YAML**:
```yaml
esphome:
  name: respeaker-xvf3800-assistant  # This becomes the mDNS name
```

**Benefits**:
- IP can change freely
- No need to track IPs
- Works with DHCP

### 6. Backup Your Configuration

**Docker volumes persist**, but backup anyway:
```bash
# Backup ESPHome configs
tar -czf esphome-backup-$(date +%Y%m%d).tar.gz esphome/

# Restore
tar -xzf esphome-backup-20251229.tar.gz
```

---

## Quick Reference Card

**Most Common Commands**:
```bash
# Upload firmware
docker exec esphome esphome upload /config/respeaker.yaml --device respeaker-xvf3800-assistant.local

# View logs
docker exec esphome esphome logs /config/respeaker.yaml

# Validate config
docker exec esphome esphome config /config/respeaker.yaml

# Check container status
docker ps | grep esphome

# Restart container
docker restart esphome

# Find device IP
avahi-resolve -n respeaker-xvf3800-assistant.local
```

**File Locations**:
```
Host:       ./esphome/respeaker.yaml
Container:  /config/respeaker.yaml
Web UI:     http://192.168.2.65:6052/
```

**Network**:
```
Device hostname: respeaker-xvf3800-assistant.local
OTA port:        3232
ESPHome API:     6053
```

---

## Learning Resources

### ESPHome Documentation
- [ESPHome Official Docs](https://esphome.io/)
- [ESPHome Voice Assistant](https://esphome.io/components/voice_assistant/)
- [ESPHome I2S Audio](https://esphome.io/components/i2s_audio.html)

### Docker Basics
- [Docker Exec Reference](https://docs.docker.com/engine/reference/commandline/exec/)
- [Docker Compose](https://docs.docker.com/compose/)

### Home Assistant
- [Home Assistant ESPHome Integration](https://www.home-assistant.io/integrations/esphome/)
- [Voice Assistants in HA](https://www.home-assistant.io/voice_control/)

---

## Summary

### Key Takeaways

1. **Always use `docker exec esphome` prefix** for ESPHome commands
2. **Use container paths** (`/config/`) in docker exec commands
3. **Edit files on host** in `./esphome/` directory
4. **Use hostnames** (`.local`) instead of IP addresses
5. **Web UI at port 6052** is easier than command-line for basic tasks

### What You Learned

✅ Why Docker is used for ESPHome
✅ How file paths map between host and container
✅ How to upload firmware via OTA
✅ How to troubleshoot network issues
✅ How to use mDNS hostnames
✅ How to view logs and debug

### Next Steps

- Bookmark ESPHome dashboard: `http://192.168.2.65:6052/`
- Create bash alias for easier commands
- Learn YAML configuration basics
- Explore ESPHome components documentation

---

**You now understand the Docker + ESPHome setup!** 🐳

The "magic" of `docker exec` is that it runs commands **inside** the container where ESPHome is installed, while you edit files **outside** on your Pi where they're easier to access. The volume mount keeps them in sync automatically.
