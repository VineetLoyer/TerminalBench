.PHONY: install test serve web dry-run sandbox-image

install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"
	npm --prefix apps/web install

test:
	.venv/bin/pytest

serve:
	.venv/bin/terminalbench serve --port 8741

web:
	npm --prefix apps/web run dev -- --port 8742 --hostname 0.0.0.0

dry-run:
	.venv/bin/terminalbench train --dry-run --out runs/prepare

sandbox-image:
	docker build -f docker/sandbox.Dockerfile -t terminalbench-sandbox .
