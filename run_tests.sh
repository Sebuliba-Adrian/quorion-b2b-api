#!/bin/bash
# Quick test runner script

source venv/bin/activate
echo "Running all tests..."
pytest commerce/tests.py -v --cov=commerce --cov-report=term-missing
echo ""
echo "Test summary:"
echo "- All 13 tests should pass"
echo "- Coverage should be ~94%"

