# IFP Edge - Intelligent Infrastructure Monitoring

<div align="center">

![IFP Edge](https://img.shields.io/badge/IFP-Edge-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-Apache%202.0-green?style=for-the-badge)
![Docker](https://img.shields.io/badge/docker-required-blue?style=for-the-badge)

**Lightweight DevOps monitoring with intelligent anomaly detection**

[Website](https://infinity-folder.no) • [Documentation](#quick-start) • [Demo Video](#demo)

</div>

---

## What is IFP Edge?

IFP Edge is a **lightweight, self-contained DevOps monitoring stack** that runs anywhere Docker runs. No cloud dependencies, no vendor lock-in, no complex setup.

### Key Features

✅ **Real-time Monitoring** - Track services, infrastructure, and applications
✅ **Intelligent Alerts** - ML-based anomaly detection (not just threshold alerts)
✅ **Web3 Integration** - Optional blockchain wallet monitoring
✅ **5-Minute Setup** - Docker Compose, no complex configuration
✅ **Edge-First** - Runs on Raspberry Pi to production servers

### What Makes IFP Different?

- **Transparent**: We show you exactly why alerts fire (no black box AI)
- **Honest**: We don't over-promise autonomous magic
- **Edge-Native**: Designed for resource-constrained environments
- **Privacy-First**: Your metrics never leave your infrastructure

---

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose
- 2GB RAM minimum (4GB recommended)
- Linux/macOS/Windows with WSL2

### Installation (5 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/Nordvei/ifp-edge.git
cd ifp-edge

# 2. Start IFP Edge
./quick-start.sh

# 3. Access dashboards
# Grafana: http://localhost:3003 (admin/admin)
# Prometheus: http://localhost:9091
# Demo App: http://localhost:8081
# O2 Wallet: http://localhost:8086
```

That's it! IFP Edge is now monitoring your infrastructure.

> **Note**: Using alternative ports (3003, 9091, 8081, 8086) to avoid conflicts if you're running other services.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    IFP Edge Stack                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Grafana    │◄─────┤  Prometheus  │               │
│  │  Dashboard   │      │   Metrics    │               │
│  └──────────────┘      └───────▲──────┘               │
│                                │                        │
│                                │                        │
│  ┌──────────────┐      ┌──────┴──────┐               │
│  │     SAGE     │─────►│  Your Apps  │               │
│  │  (AI Monitor)│      │  & Services │               │
│  └──────────────┘      └─────────────┘               │
│                                                         │
│  ┌──────────────┐      Optional:                      │
│  │  O2 Wallet   │      Blockchain monitoring          │
│  │   Monitor    │      (Polygon network)              │
│  └──────────────┘                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **Prometheus** - Time-series metrics storage
2. **Grafana** - Visualization dashboards
3. **SAGE** - Intelligent monitoring agent (IFP's AI layer)
4. **O2 Wallet** - Optional Web3 wallet monitoring
5. **Demo App** - Sample application for testing

---

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Grafana
GRAFANA_PASSWORD=your_secure_password

# SAGE Monitoring
SAGE_CHECK_INTERVAL=30  # Check every 30 seconds
LOG_LEVEL=INFO

# Web3 (Optional)
WALLET_ADDRESS=0x...    # Your wallet address to monitor
POLYGON_RPC_URL=https://polygon-rpc.com
```

### Monitoring Your Services

IFP Edge auto-discovers services with these labels:

```yaml
# In your docker-compose.yml
services:
  your-app:
    image: your-app:latest
    labels:
      - "ifp.monitor=true"        # Enable monitoring
      - "ifp.tier=production"     # Environment tier
```

---

## Usage Examples

### Example 1: Monitor Nginx

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    labels:
      - "ifp.monitor=true"
      - "ifp.tier=production"
```

### Example 2: Monitor PostgreSQL

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
    labels:
      - "ifp.monitor=true"
      - "ifp.tier=database"
```

### Example 3: Web3 Wallet Monitoring

```bash
# Set your wallet address in .env
WALLET_ADDRESS=0x638C70f337fc63DB0E108308E3dD60f71eb97342

# IFP will:
# - Track token balance
# - Predict when wallet will run dry
# - Alert 30 minutes before depletion
```

---

## Dashboards

### Default Dashboards

IFP Edge includes pre-built dashboards:

1. **System Overview** - CPU, memory, disk, network
2. **Service Health** - Uptime, response times, errors
3. **O2 Wallet** - Token balance, drain rate, predictions
4. **SAGE Insights** - AI-detected anomalies and patterns

Access: http://localhost:3003 (login: admin/admin)

---

## Monitoring Capabilities

### What SAGE Monitors

✅ **Service Health**
- Uptime and availability
- Response time degradation
- Error rate spikes

✅ **Resource Usage**
- CPU and memory trends
- Disk space predictions
- Network anomalies

✅ **Web3 (Optional)**
- Token wallet balance
- Drain rate calculation
- Time-to-empty predictions

### Intelligent Alerts

SAGE uses pattern detection (not just thresholds):

- **Anomaly Detection**: Detects unusual behavior patterns
- **Predictive Alerts**: Warns before problems occur
- **Reduced Noise**: Fewer false positives than traditional monitoring

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker daemon
docker ps

# Check logs
docker compose logs

# Reset and restart
docker compose down -v
docker compose up -d
```

### High Memory Usage

```bash
# Reduce Prometheus retention
# Edit docker-compose.yml:
# '--storage.tsdb.retention.time=3d'  # Instead of 7d

# Restart
docker compose restart prometheus
```

### Can't Access Dashboards

```bash
# Check ports
docker compose ps

# Verify services are running
docker compose logs grafana
docker compose logs prometheus
```

---

## Roadmap

### Current (Edge v1.0)
- ✅ Core monitoring stack
- ✅ SAGE intelligent agent
- ✅ Web3 wallet monitoring
- ✅ Grafana dashboards

### Coming Soon (Edge v1.1)
- 🔄 Pattern discovery service
- 🔄 Automatic remediation (recommend-only mode)
- 🔄 Multi-node federation
- 🔄 Enhanced ML models

### Future (Edge v2.0)
- ⏳ Drone integration (infrastructure inspection)
- ⏳ GPU acceleration (Nvidia DGX Spark)
- ⏳ Advanced predictive analytics
- ⏳ Enterprise SSO

---

## Demo

### Live Demo

🎥 **[Watch 2-Minute Demo Video](#)** *(coming soon)*

See IFP Edge in action:
- Real-time monitoring
- Anomaly detection
- Web3 wallet predictions
- Dashboard walkthrough

### Try It Yourself

Spin up the demo in 30 seconds:

```bash
git clone https://github.com/Nordvei/ifp-edge.git
cd ifp-edge
./quick-start.sh
open http://localhost:3003
```

---

## FAQ

### Q: What's the difference between IFP Edge and full IFP?

**IFP Edge** is the lightweight, open-source version that runs anywhere.
**IFP Full** includes GPU acceleration, advanced ML, and enterprise features.

Think: PostgreSQL (Edge) vs. PostgreSQL Enterprise (Full)

### Q: Do I need a GPU?

No! IFP Edge runs on CPU-only. GPU features come later in IFP Full.

### Q: What about privacy?

**All data stays local.** IFP Edge doesn't phone home, doesn't send telemetry, doesn't require cloud connectivity (except optional blockchain RPC).

### Q: Can I use this in production?

Yes, but **IFP Edge is early-stage software**. Use for:
- ✅ Development environments
- ✅ Staging/test environments
- ✅ Non-critical production workloads
- ⚠️ Production (with monitoring and backups)

### Q: How do I get support?

- GitHub Issues: Bug reports and feature requests
- Discussions: Questions and community help
- Website: https://infinity-folder.no

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repo
git clone https://github.com/Nordvei/ifp-edge.git
cd ifp-edge

# Build from source
docker compose up --build

# Run tests
./scripts/test.sh
```

---

## License

IFP Edge is licensed under the [Apache License 2.0](LICENSE).

**Commercial licenses** available for IFP Full (GPU-accelerated version).

---

## Credits

Built with:
- [Prometheus](https://prometheus.io/) - Metrics
- [Grafana](https://grafana.com/) - Dashboards
- [Docker](https://docker.com/) - Containers
- [Python](https://python.org/) - SAGE AI agent

---

## Links

- **Website**: https://infinity-folder.no
- **GitHub**: https://github.com/Nordvei/ifp-edge
- **Issues**: https://github.com/Nordvei/ifp-edge/issues
- **Twitter**: *@InfinityFolder* *(coming soon)*

---

<div align="center">

**Made with ❤️ by the IFP Team**

[⭐ Star us on GitHub](https://github.com/Nordvei/ifp-edge) if you find IFP Edge useful!

</div>
