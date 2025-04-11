include ../../../../Makefile.shared-python-uv

test-unit: venv-dev
	uv run pytest tests/unit --disable-warnings -v

test-component: venv-dev
	@echo "test-component not available"

test-integration: venv-dev
	uv run pytest tests/integration --disable-warnings -v
