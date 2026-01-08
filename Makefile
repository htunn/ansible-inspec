# Makefile for ansible-inspec

.PHONY: help install dev-install test lint format clean build docker-build docker-run publish-test publish

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install package
	pip install -e .

dev-install:  ## Install package with dev dependencies
	pip install -e ".[dev]"

test:  ## Run tests
	pytest tests/ -v --cov=ansible_inspec --cov-report=term-missing

lint:  ## Run linting
	flake8 lib/ tests/
	mypy lib/

format:  ## Format code
	black lib/ tests/
	isort lib/ tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

docker-build:  ## Build Docker image
	docker build -t ansible-inspec:local .

docker-run:  ## Run Docker container
	docker run --rm ansible-inspec:local --help

docker-test:  ## Test Docker image
	docker run --rm ansible-inspec:local --version
	docker run --rm -v $(PWD):/workspace ansible-inspec:local init profile test-docker-profile
	@test -d test-docker-profile && echo "✅ Docker test passed" || echo "❌ Docker test failed"
	@rm -rf test-docker-profile

publish-test:  ## Publish to TestPyPI
	python -m build
	twine upload --repository testpypi dist/*

publish:  ## Publish to PyPI (use git tags instead)
	@echo "⚠️  Use 'git tag -a vX.Y.Z -m \"Release X.Y.Z\"' and 'git push origin vX.Y.Z' instead"
	@echo "This will trigger automated publishing via GitHub Actions"

version:  ## Show current version
	@python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"

.DEFAULT_GOAL := help
