# Makefile for aidoctool

.PHONY: test lint format coverage

# Run all tests with pytest
test:
	PYTHONPATH=. pytest tests

# Run tests with coverage report
coverage:
	PYTHONPATH=. pytest --cov=aidoctool tests/ --cov-report=term --cov-report=html
	@echo "HTML coverage report generated in htmlcov/"

# Lint with flake8
lint:
	flake8 aidoctool

# Format with black
format:
	black aidoctool
