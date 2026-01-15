# Contributing to Cybersecurity Agent Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this polyglot cybersecurity platform.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Contribution Guidelines](#contribution-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Local orchestration |
| Go | 1.21+ | Gateway service |
| Python | 3.11+ | Brain service |
| Rust | 1.70+ | Core scanner |
| Node.js | 18+ | Dashboard |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Caching |

### Quick Start

```bash
# Clone the repository
git clone https://github.com/csa7mdm/Cypersecurity.git
cd Cypersecurity

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Run tests
./scripts/run-tests.sh
```

## Development Setup

### Gateway (Go)

```bash
cd gateway
go mod download
go build ./cmd/gateway
go test ./...
```

### Brain (Python)

```bash
cd brain
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

### Core Scanner (Rust)

```bash
cd core
cargo build
cargo test
cargo clippy
```

### Dashboard (React/TypeScript)

```bash
cd dashboard
npm install
npm run dev
npm test
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Dashboard (React)                     │
├─────────────────────────────────────────────────────────┤
│                    Gateway (Go/Gin)                      │
│              JWT Auth, RBAC, Rate Limiting               │
├─────────────────┬───────────────────┬───────────────────┤
│   Brain (Py)    │   Core (Rust)     │   Database (PG)   │
│   AI Analysis   │   Fast Scanning   │   Multi-tenant    │
└─────────────────┴───────────────────┴───────────────────┘
```

## Contribution Guidelines

### Types of Contributions

1. **Bug Fixes**: Fix issues reported in GitHub Issues
2. **Features**: Implement features from the roadmap or propose new ones
3. **Documentation**: Improve docs, add examples, fix typos
4. **Tests**: Add missing tests, improve coverage
5. **Performance**: Optimize algorithms, reduce resource usage

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/add-nmap-scanner` |
| Bug Fix | `fix/description` | `fix/auth-token-expiry` |
| Docs | `docs/description` | `docs/api-examples` |
| Refactor | `refactor/description` | `refactor/scanner-module` |

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
3. **Make** your changes with clear commit messages
4. **Add/Update** tests for your changes
5. **Run** the full test suite locally
6. **Update** documentation if needed
7. **Submit** a pull request

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
- [ ] Commits are signed (if required)

## Testing Requirements

### Minimum Coverage

| Service | Required Coverage |
|---------|-------------------|
| Gateway (Go) | 70% |
| Brain (Python) | 80% |
| Core (Rust) | 70% |
| Dashboard | 60% |

### Test Types

```bash
# Unit tests
go test ./...
pytest tests/unit/
cargo test

# Integration tests
pytest tests/integration/

# E2E tests
cd e2e_tests && npx playwright test
```

## Code Style

### Go

- Follow [Effective Go](https://golang.org/doc/effective_go)
- Use `gofmt` and `golangci-lint`
- Maximum line length: 120 characters

### Python

- Follow PEP 8
- Use `ruff` for linting
- Use `mypy` for type checking
- Docstrings for public functions

### Rust

- Follow Rust idioms
- Use `cargo fmt` and `cargo clippy`
- Document public APIs

### TypeScript

- Follow project ESLint configuration
- Use TypeScript strict mode
- Prefer functional components with hooks

## Questions?

- Open a GitHub Discussion for questions
- Check existing issues before creating new ones
- Join our community chat (if available)

---

Thank you for contributing!
