# IFP Terminal Workspace Setup

This document describes the IFP Terminal Workspace project created for command-line interaction with IFP Edge.

## Overview

The IFP Terminal Workspace is a separate Node.js/TypeScript project that provides CLI tools and programmatic access to IFP Edge monitoring infrastructure.

## Location

The workspace has been created at: `~/ifp-terminal-workspace`

## Features

- **CLI Interface**: Command-line tools for managing IFP Edge instances
- **Library API**: Programmatic access to monitoring data
- **Real-time Monitoring**: Terminal-based monitoring dashboard
- **Service Management**: View and manage monitored services
- **Alert Management**: View and manage alerts

## Quick Start

```bash
# Navigate to the workspace
cd ~/ifp-terminal-workspace

# Install dependencies
npm install

# Build the project
npm run build

# Run CLI commands
npm start
```

## CLI Commands

The workspace provides the following CLI commands:

- `ifp status` - Check IFP Edge instance status
- `ifp services` - List all monitored services
- `ifp alerts` - View recent alerts
- `ifp monitor` - Real-time monitoring dashboard

## Integration with IFP Edge

The terminal workspace connects to your IFP Edge instance via:

- **Grafana API**: `http://localhost:3003`
- **Prometheus API**: `http://localhost:9091`

Ensure your IFP Edge instance is running before using the workspace tools.

## Development

```bash
cd ~/ifp-terminal-workspace

# Install dependencies
npm install

# Run in development mode
npm run dev

# Run tests
npm test

# Lint and format
npm run lint
npm run format
```

## Project Structure

```
~/ifp-terminal-workspace/
├── src/
│   ├── cli.ts           # CLI entry point
│   ├── index.ts         # Library API
│   └── ...
├── tests/               # Test files
├── dist/                # Compiled output
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
└── README.md            # Full documentation
```

## Next Steps

1. Install dependencies: `cd ~/ifp-terminal-workspace && npm install`
2. Build the project: `npm run build`
3. Start your IFP Edge instance: `./quick-start.sh` (from ifp-edge directory)
4. Test the CLI: `cd ~/ifp-terminal-workspace && npm start`

## Documentation

Full documentation is available in the workspace README:
- Location: `~/ifp-terminal-workspace/README.md`

## License

Apache License 2.0 (same as IFP Edge)
