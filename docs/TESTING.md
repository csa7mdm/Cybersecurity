# Cyper Security Agent - Testing Guide

## Quick Start Testing

### 1. Start Services with Docker Compose

```bash
# Copy environment variables
cp .env.example .env

# Edit .env and set your API keys
nano .env

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f gateway
```

### 2. Initialize Database

```bash
# If using Docker Compose, the database is auto-initialized
# For local PostgreSQL:
./scripts/init-db.sh
```

### 3. Run Tests

```bash
# Wait for services to start (about 30 seconds)
sleep 30

# Run test suite
./scripts/test.sh
```

## Manual Testing

### Health Check

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-30T15:00:00Z",
  "version": "0.1.0"
}
```

### User Registration

```bash
curl -X POST http://localhost:8080/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'
```

### Accept Terms of Use

```bash
curl -X POST http://localhost:8080/v1/auth/accept-terms \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id-from-registration",
    "terms_version": "1.0",
    "acceptance_ip": "127.0.0.1"
  }'
```

### Login

```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cyper.security",
    "password": "Admin123!"
  }'
```

Save the `access_token` from the response.

### Access Protected Endpoint

```bash
# Use the token from login
TOKEN="your-access-token-here"

curl -X GET http://localhost:8080/v1/auth/pulse \
  -H "Authorization: Bearer $TOKEN"
```

## Database Testing

### Connect to Database

```bash
# Via Docker
docker-compose exec postgres psql -U cyper_admin -d cyper_security

# Local PostgreSQL
psql -h localhost -U cyper_admin -d cyper_security
```

### Verify Tables

```sql
-- List all tables
\dt

-- Check user count
SELECT COUNT(*) FROM users;

-- View admin user
SELECT id, email, username, role FROM users WHERE email = 'admin@cyper.security';

-- Check audit logs
SELECT action, status, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 10;
```

## Component Testing

### Test Rust Core

```bash
cd core
cargo test
cargo run
```

### Test Go Gateway

```bash
cd gateway
go test ./...
go run cmd/server/main.go
```

### Test Python Brain

```bash
cd brain
pip install -e .
pytest
```

### Test Dashboard

```bash
cd dashboard
npm install
npm run dev
```

## Integration Testing

### Full Stack Test

1. Start all services: `docker-compose up -d`
2. Initialize database: `./scripts/init-db.sh` (if needed)
3. Test authentication: `./scripts/test.sh`
4. Access dashboard: `http://localhost:3000`
5. Check logs: `docker-compose logs -f`

## Performance Testing

### Load Test Authentication

```bash
# Install apache bench if not available
# macOS: brew install httpd
# Ubuntu: sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8080/health

# Test login endpoint
ab -n 100 -c 5 -p login.json -T application/json \
  http://localhost:8080/v1/auth/login
```

## Security Testing

### Test Unauthorized Access

```bash
# Should fail
curl http://localhost:8080/v1/auth/pulse

# Should return "missing authorization header"
```

### Test Invalid Token

```bash
curl -H "Authorization: Bearer invalid-token" \
  http://localhost:8080/v1/auth/pulse

# Should return "invalid token"
```

### Test SQL Injection (Should be protected)

```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cyper.security",
    "password": "'\'' OR '\''1'\''='\''1"
  }'

# Should fail with "invalid credentials"
```

## Troubleshooting

### Services won't start

```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart gateway
```

### Database connection failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres pg_isready

# View PostgreSQL logs
docker-compose logs postgres
```

### Gateway won't compile

```bash
cd gateway
go mod tidy
go mod download
go build ./cmd/server
```

## Monitoring

### View All Logs

```bash
docker-compose logs -f
```

### View Specific Service

```bash
docker-compose logs -f gateway
docker-compose logs -f brain
docker-compose logs -f core
```

### Database Queries

```bash
# Active sessions
docker-compose exec postgres psql -U cyper_admin -d cyper_security \
  -c "SELECT COUNT(*) FROM sessions WHERE revoked_at IS NULL"

# Recent audit logs
docker-compose exec postgres psql -U cyper_admin -d cyper_security \
  -c "SELECT action, severity, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 10"
```

## Cleanup

### Stop Services

```bash
docker-compose down
```

### Remove Volumes (WARNING: Deletes all data)

```bash
docker-compose down -v
```

### Clean Build Artifacts

```bash
# Rust
cd core && cargo clean

# Go
cd gateway && go clean

# Python
cd brain && rm -rf build/ dist/ *.egg-info

# Node
cd dashboard && rm -rf node_modules/ build/
```
