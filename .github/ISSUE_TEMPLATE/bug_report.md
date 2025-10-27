---
name: Bug Report
about: Report a bug to help us improve IFP Edge
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## Environment
- **OS**: (e.g., Ubuntu 22.04, macOS 13.0, Windows 11 WSL2)
- **Docker Version**: (run `docker --version`)
- **Docker Compose Version**: (run `docker compose version`)
- **IFP Edge Version**: (e.g., v1.0.0)

## Steps to Reproduce
1. Run `docker compose up -d`
2. Access Grafana at http://localhost:3001
3. Try to login
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Logs
Please include relevant log output:

```bash
# Get logs
docker compose logs

# Or for specific service
docker compose logs sage
```

Paste logs here:
```
[Paste logs here]
```

## Screenshots
If applicable, add screenshots to help explain your problem.

## Additional Context
Add any other context about the problem here.
