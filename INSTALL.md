# IFP Edge - Installation Guide

Get IFP Edge running in **5 minutes** or less.

---

## Prerequisites

### System Requirements

**Minimum**:
- 2 GB RAM
- 2 CPU cores
- 10 GB disk space
- Docker 20.10+
- Docker Compose 2.0+

**Recommended**:
- 4 GB RAM
- 4 CPU cores
- 20 GB disk space (for metrics retention)

### Supported Platforms

- ✅ Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- ✅ macOS (Intel and Apple Silicon)
- ✅ Windows 11 with WSL2
- ✅ Raspberry Pi 4 (4GB+ RAM)

---

## Quick Install

### 1. Install Docker

**Ubuntu/Debian**:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

**macOS**:
```bash
brew install --cask docker
# Or download from https://docker.com
```

**Windows**:
- Install Docker Desktop: https://docker.com/products/docker-desktop

### 2. Clone IFP Edge

```bash
git clone https://github.com/Nordvei/ifp-edge.git
cd ifp-edge
```

### 3. Configure

```bash
# Copy example environment file
cp .env.example .env

# (Optional) Edit configuration
nano .env
```

**Minimum Configuration**:
```bash
# Set a secure Grafana password
GRAFANA_PASSWORD=your_secure_password_here
```

**Web3 Monitoring** (Optional):
```bash
# Add your wallet address
WALLET_ADDRESS=0x638C70f337fc63DB0E108308E3dD60f71eb97342
```

### 4. Start IFP Edge

```bash
docker compose up -d
```

### 5. Verify Installation

```bash
# Check all services are running
docker compose ps

# You should see:
# - ifp-prometheus
# - ifp-grafana
# - ifp-sage
# - ifp-o2-wallet (if Web3 enabled)
# - ifp-demo-app
```

### 6. Access Dashboards

Open in your browser:

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: (what you set in .env)

- **Prometheus**: http://localhost:9090

- **O2 Wallet API**: http://localhost:8085/docs

---

## Post-Installation

### Import Dashboards

1. Open Grafana: http://localhost:3001
2. Login (admin/admin)
3. Go to **Dashboards** → **Import**
4. Upload `dashboards/ifp-overview.json`
5. Select **Prometheus** as data source

### Verify SAGE is Monitoring

```bash
# Check SAGE logs
docker compose logs sage

# You should see:
# "👁️  OBSERVE: Gathering system telemetry..."
# "🧠 REFLECT: Analyzing system state..."
# "✅ No actions needed - system healthy"
```

### Test Alerting

Trigger a test alert:

```bash
# Simulate high CPU usage
docker run --rm -d --name stress-test alpine:latest sh -c 'while true; do :; done'

# Wait 1-2 minutes, then check SAGE logs
docker compose logs sage | grep -i "alert\|warning"

# Clean up
docker stop stress-test
```

---

## Configuration Guide

### Grafana Dashboards

**Pre-built dashboards** in `dashboards/`:
- `ifp-overview.json` - System overview
- `service-health.json` - Service monitoring
- `o2-wallet.json` - Web3 wallet tracking

**Import dashboards**:
```bash
# Via Grafana UI: Dashboards → Import → Upload JSON
# Or auto-provision by editing:
nano config/grafana-dashboards.yml
```

### Prometheus Targets

**Add your services** to monitor in `config/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['my-app:8080']
        labels:
          service: 'my-app'
          tier: 'production'
```

Then restart:
```bash
docker compose restart prometheus
```

### SAGE Configuration

**Adjust monitoring interval** in `.env`:

```bash
# Check every 10 seconds (more frequent)
SAGE_CHECK_INTERVAL=10

# Check every 60 seconds (less frequent, lower CPU)
SAGE_CHECK_INTERVAL=60
```

**Change alert threshold** for Web3:

```bash
# Alert when wallet has < 60 minutes remaining
TTE_ALERT_MINUTES=60
```

---

## Monitoring Your Applications

### Method 1: Docker Labels (Recommended)

Add labels to your services in `docker-compose.yml`:

```yaml
services:
  my-app:
    image: my-app:latest
    ports:
      - "8080:8080"
    labels:
      - "ifp.monitor=true"        # Enable monitoring
      - "ifp.tier=production"     # Environment
      - "prometheus.port=8080"    # Metrics port
      - "prometheus.path=/metrics" # Metrics endpoint
```

### Method 2: Prometheus Config

Edit `config/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-database'
    static_configs:
      - targets: ['postgres:9187']  # postgres_exporter
```

### Method 3: Service Discovery

For Kubernetes or cloud environments:

```yaml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
```

---

## Troubleshooting

### Services Won't Start

**Check Docker**:
```bash
docker --version
docker compose version

# Should be Docker 20.10+ and Compose 2.0+
```

**Check logs**:
```bash
docker compose logs

# Or specific service:
docker compose logs grafana
```

**Reset everything**:
```bash
docker compose down -v
docker compose up -d
```

### Can't Access Grafana

**Check if port 3001 is free**:
```bash
lsof -i :3001

# If port is taken, change in docker-compose.yml:
# ports:
#   - "3002:3000"  # Use port 3002 instead
```

**Check firewall** (Linux):
```bash
sudo ufw allow 3001
```

### High Memory Usage

**Reduce Prometheus retention**:

Edit `docker-compose.yml`:
```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=3d'  # Instead of 7d
```

**Limit container memory**:
```yaml
prometheus:
  deploy:
    resources:
      limits:
        memory: 512M
```

### SAGE Not Detecting Services

**Check Prometheus targets**:
1. Open http://localhost:9090/targets
2. Verify all targets are "UP"
3. If DOWN, check service connectivity

**Check SAGE logs**:
```bash
docker compose logs sage

# Look for:
# "Found X Prometheus targets"
# "Services: X"
```

### Web3 Monitoring Not Working

**Check wallet address** in `.env`:
```bash
# Must be valid Ethereum address (0x...)
WALLET_ADDRESS=0x638C70f337fc63DB0E108308E3dD60f71eb97342
```

**Test O2 Wallet API**:
```bash
curl http://localhost:8085/api/balance
```

**Check blockchain RPC**:
```bash
# If Polygon RPC is slow, try alternative:
POLYGON_RPC_URL=https://rpc-mainnet.matic.quiknode.pro
```

---

## Updating IFP Edge

### Pull Latest Changes

```bash
cd ifp-edge
git pull origin main
```

### Rebuild Services

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Preserve Data

Metrics and dashboards are stored in Docker volumes and **persist across updates**.

**Backup volumes** (optional):
```bash
docker run --rm -v ifp-edge_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
```

---

## Uninstall

### Remove IFP Edge

```bash
cd ifp-edge

# Stop and remove containers
docker compose down

# Remove data volumes (WARNING: deletes metrics)
docker compose down -v
```

### Remove Docker Images

```bash
docker rmi $(docker images 'ifp-*' -q)
```

---

## Next Steps

✅ **Installed IFP Edge** → Congrats!

**What's next?**

1. 📊 **Explore Dashboards**: http://localhost:3001
2. 🔔 **Set up Alerts**: Configure Grafana alerts for your services
3. 🌐 **Add Web3 Monitoring**: Set your `WALLET_ADDRESS` in `.env`
4. 📖 **Read the Docs**: Learn about SAGE's intelligent monitoring
5. 🤝 **Join Community**: GitHub Discussions for questions

---

## Getting Help

- **GitHub Issues**: https://github.com/Nordvei/ifp-edge/issues
- **Discussions**: https://github.com/Nordvei/ifp-edge/discussions
- **Website**: https://infinity-folder.no

---

**Happy Monitoring!** 🚀
