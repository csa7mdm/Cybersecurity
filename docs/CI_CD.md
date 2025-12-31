# Quality & Reliability Infrastructure

This directory contains automated quality assurance infrastructure.

## CI/CD Pipeline

### Workflows

**`.github/workflows/ci-cd.yml`**
- Runs on every push and pull request
- Jobs:
  1. **Test Brain Service** (Python)
     - Linting with ruff
     - Type checking with mypy
     - Unit tests with pytest
     - Coverage reporting (Codecov)
  
  2. **Test Gateway Service** (Go)
     - Linting with golangci-lint
     - Unit tests with race detection
     - Coverage reporting
  
  3. **Security Scanning**
     - Trivy vulnerability scanner
     - Python dependency check (safety)
     - SARIF upload to GitHub Security
  
  4. **Build Docker Images**
     - Build Brain and Gateway images
     - Cache layers for speed
  
  5. **E2E Tests** (main branch only)
     - Playwright browser tests
     - Full workflow validation
  
  6. **Deploy to Staging** (main branch only)
     - Kubernetes deployment
     - Smoke tests

**`.github/workflows/deploy-production.yml`**
- Triggers on release publication
- Builds and pushes Docker images
- Deploys to production Kubernetes
- Runs production smoke tests
- Notifies Slack

### Branch Protection

**Main branch**:
- Require PR reviews (2 approvers)
- Require status checks to pass
- Require branches to be up to date
- Require signed commits

## E2E Testing

### Setup

```bash
# Install dependencies
pip install playwright pytest-playwright

# Install browsers
playwright install chromium
```

### Running Tests

```bash
# Run all E2E tests
pytest e2e_tests/ -v

# Run specific test
pytest e2e_tests/test_platform.py::TestUserOnboarding::test_signup_and_verification

# Run smoke tests only
pytest e2e_tests/ -m smoke

# Run with headed browser (see what's happening)
pytest e2e_tests/ --headed
```

### Test Coverage

E2E tests cover:
- User onboarding (signup, verification, wizard)
- Scan workflows (create, run, view results)
- Report generation (PDF download)
- Integrations (Slack, webhooks)
- Billing (upgrade, subscription)
- Team collaboration (invitations)

## Monitoring

### Metrics Tracked

- Test success rate
- Code coverage (target: 80%+)
- Performance benchmarks
- Dependency vulnerabilities
- Docker image sizes

### Alerts

- Failed deployments → Slack
- Security vulnerabilities → GitHub Security
- Low test coverage → PR comments

## Performance Testing

### Load Testing

Use k6 for load testing:

```bash
k6 run performance_tests/load_test.js
```

**Targets**:
- API: 1000 req/s
- Scan creation: < 500ms p95
- Report generation: < 10s p95

## Deployment Strategy

### Staging
- Auto-deploy on main branch merge
- Pre-production environment
- Full feature parity with production

### Production
- Manual release via GitHub Releases
- Blue-green deployment
- Automatic rollback on failure
- 5-minute deployment window

## Security

### Secrets Management

Store in GitHub Secrets:
- `KUBE_CONFIG_STAGING`
- `KUBE_CONFIG_PRODUCTION`
- `SLACK_WEBHOOK_URL`
- API keys for external services

### Image Scanning

All Docker images scanned for:
- CVEs (Trivy)
- Misconfigurations
- Secrets in layers

## Troubleshooting

### CI Failures

**Tests failing**:
1. Check test logs in GitHub Actions
2. Run locally: `pytest tests/ -v`
3. Check for environment differences

**Build failures**:
1. Check Docker build logs
2. Verify dependencies in requirements.txt/go.mod
3. Clear cache and rebuild

**Deployment failures**:
1. Check Kubernetes logs: `kubectl logs -n staging deployment/brain-deployment`
2. Verify secrets are set
3. Check resource limits

### E2E Test Failures

**Screenshots available** at:
- GitHub Actions → Artifacts → playwright-screenshots

**Re-run failed test**:
```bash
pytest e2e_tests/test_platform.py::TestName::test_method --headed
```

## Future Improvements

- [ ] Visual regression testing
- [ ] Performance regression detection
- [ ] Automated rollback on metrics degradation
- [ ] Canary deployments
- [ ] Multi-region deployment
