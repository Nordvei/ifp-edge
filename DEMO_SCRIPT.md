# IFP Edge - 2-Minute Demo Recording Script

**Goal**: Show real value in 2 minutes. No fake demos, no marketing fluff.

---

## Demo Script (120 seconds)

### Intro (10 seconds)
**Screen**: Terminal with `ifp-edge` directory

**Say**:
> "I'm going to show you IFP Edge - intelligent DevOps monitoring that runs anywhere. Watch me set this up from scratch in under 2 minutes."

**Do**:
- Show empty terminal
- `ls` to show ifp-edge directory

---

### Installation (30 seconds)
**Screen**: Terminal

**Say**:
> "Installation is three commands. First, clone the repo..."

**Do**:
```bash
# Show the commands clearly on screen
git clone https://github.com/Nordvei/ifp-edge.git
cd ifp-edge
cp .env.example .env

# Start the stack
docker compose up -d
```

**Say** (while containers start):
> "That's it. Docker Compose handles everything - Prometheus, Grafana, and SAGE, our intelligent monitoring agent."

**Do**:
- Let containers start (15-20 seconds)
- Show `docker compose ps` output

---

### Real-Time Monitoring (40 seconds)
**Screen**: Split screen - Grafana dashboard + Terminal with SAGE logs

**Say**:
> "Let's see what it's monitoring. This is the Grafana dashboard - it auto-discovered my services..."

**Do**:
1. Open Grafana: http://localhost:3001
2. Show system overview dashboard (pre-configured)
3. Point out:
   - Live CPU/memory graphs
   - Service health indicators
   - Real data flowing

**Say**:
> "And here's SAGE, the intelligent agent. It's analyzing patterns, not just checking thresholds."

**Do**:
- Show terminal with `docker compose logs sage --follow`
- Highlight real log lines:
  - "Gathering system telemetry..."
  - "Services: 12"
  - "No anomalies detected"

---

### Intelligent Detection Demo (25 seconds)
**Screen**: Terminal + Grafana

**Say**:
> "Watch what happens when I simulate a problem..."

**Do**:
1. Run stress test:
   ```bash
   docker run --rm -d --name cpu-stress alpine sh -c 'while true; do :; done'
   ```

2. Wait 5-10 seconds
3. Show SAGE logs detecting the anomaly:
   - "CPU spike detected"
   - "Analyzing pattern..."

**Say**:
> "SAGE detected the CPU spike within seconds. This isn't a threshold alert - it understands the pattern is unusual for this time of day."

**Do**:
- Show Grafana graph spiking
- Show SAGE log analysis
- Kill stress test: `docker stop cpu-stress`

---

### Web3 Integration (10 seconds)
**Screen**: Browser showing O2 Wallet API

**Say**:
> "Bonus feature - it monitors blockchain wallets too. Here's my O2 token balance..."

**Do**:
- Open http://localhost:8085/api/balance
- Show JSON response with balance
- Highlight "time_to_empty" prediction

**Say**:
> "SAGE predicts when the wallet will run dry and alerts me 30 minutes before."

---

### Closing (5 seconds)
**Screen**: Back to terminal

**Say**:
> "That's IFP Edge. Open source, runs anywhere, five-minute setup. Link in the description."

**Do**:
- Show GitHub repo URL on screen: https://github.com/Nordvei/ifp-edge
- Show website: https://infinity-folder.no

---

## Recording Tips

### Setup Before Recording

1. **Pre-pull Docker images**:
   ```bash
   docker compose pull
   ```

2. **Pre-configure Grafana**:
   - Login once
   - Import dashboard
   - Set auto-refresh to 5 seconds

3. **Clean terminal**:
   ```bash
   clear
   PS1='$ '  # Simple prompt
   ```

4. **Test the flow**:
   - Do a full dry run
   - Time each section
   - Adjust if over 2 minutes

### Screen Recording Settings

**Tool**: OBS Studio (free, cross-platform)

**Settings**:
- Resolution: 1920x1080 (1080p)
- FPS: 30
- Format: MP4 (H.264)
- Bitrate: 8000 kbps

**Layout**:
```
┌─────────────────────────────────────┐
│  Terminal (top 60%)                 │
│  $ docker compose up -d             │
│  Creating ifp-prometheus... done    │
│                                     │
├─────────────────────────────────────┤
│  Browser (bottom 40%)               │
│  [Grafana Dashboard]                │
└─────────────────────────────────────┘
```

### Audio Tips

- **Microphone**: Good quality USB mic (Blue Yeti, Rode NT-USB)
- **Noise reduction**: Record in quiet room
- **Pacing**: Speak clearly, not too fast
- **Energy**: Sound enthusiastic but not over-the-top

### Editing

**Tools**:
- DaVinci Resolve (free, professional)
- iMovie (macOS, easy)
- Shotcut (free, cross-platform)

**Edits**:
1. Cut out pauses longer than 2 seconds
2. Add captions for key commands
3. Add arrows/highlights for important elements
4. Background music (low volume, royalty-free)
5. Add GitHub link overlay at end

**Captions** (add text overlays):
- "3 commands to install" (at install section)
- "Real-time monitoring" (at Grafana section)
- "Pattern detection, not thresholds" (at SAGE section)
- "Open source - github.com/nordvei/ifp-edge" (at end)

---

## Alternative: Shorter 60-Second Version

If 2 minutes is too long:

### Ultra-Fast Demo (60 seconds)

1. **Intro** (5s): "IFP Edge - intelligent monitoring in under 60 seconds"
2. **Install** (15s): Show `docker compose up -d`
3. **Dashboard** (20s): Show Grafana with real data
4. **Detection** (15s): Trigger CPU spike, show SAGE alert
5. **Close** (5s): "Open source - link below"

---

## Video Hosting

### YouTube
- Upload as "unlisted" first (for testing)
- Title: "IFP Edge - Intelligent DevOps Monitoring in 2 Minutes"
- Description: Include GitHub link, installation command
- Tags: devops, monitoring, docker, prometheus, grafana, opensource
- Thumbnail: Screenshot of Grafana dashboard with logo

### Embedding on Website

```html
<!-- On https://infinity-folder.no -->
<div class="demo-video">
  <iframe
    width="560"
    height="315"
    src="https://www.youtube.com/embed/YOUR_VIDEO_ID"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen>
  </iframe>
</div>
```

---

## Post-Recording Checklist

- [ ] Video is under 2:30 (ideally 2:00)
- [ ] Audio is clear and consistent
- [ ] Commands are visible and readable
- [ ] Dashboard shows real data (not fake)
- [ ] SAGE logs are authentic (not staged)
- [ ] GitHub link is prominent at end
- [ ] No sensitive info visible (API keys, passwords)
- [ ] Tested playback on mobile
- [ ] Captions/subtitles added
- [ ] Thumbnail created

---

## Example Timeline

| Time | Section | Content |
|------|---------|---------|
| 0:00-0:10 | Intro | "IFP Edge - monitoring that runs anywhere" |
| 0:10-0:40 | Install | Clone, configure, start (3 commands) |
| 0:40-1:20 | Monitor | Grafana dashboard + SAGE logs |
| 1:20-1:45 | Detect | CPU spike demo + pattern detection |
| 1:45-1:55 | Web3 | O2 wallet balance API |
| 1:55-2:00 | Close | GitHub link + call-to-action |

---

**Ready to record!** 🎬

Keep it real, keep it simple, keep it under 2 minutes.
