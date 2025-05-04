# Makefile for aidoctool

.PHONY: test lint format

# Run all tests with pytest
 test:
	pytest aidoctool/tests

# Lint with flake8
lint:
	flake8 aidoctool

# Format with black
format:
	black aidoctool
