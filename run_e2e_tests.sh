#!/bin/bash
# Fully automated E2E test runner
# No manual setup required!

echo "🧪 CyperSecurity Platform - Fully Automated E2E Tests"
echo "====================================================="
echo ""
echo "This will automatically:"
echo "  1. ✅ Start backend (Python/FastAPI)"
echo "  2. ✅ Start frontend (React)"
echo "  3. ✅ Wait for services to be ready"
echo "  4. ✅ Seed test data"
echo "  5. ✅ Run all E2E tests"
echo "  6. ✅ Clean up and stop services"
echo ""
echo "No manual setup required - just sit back and watch!"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Run pytest (conftest.py handles everything else)
pytest e2e_tests/ -v --tb=short

echo ""
echo "✅ Tests complete! Services have been stopped."
