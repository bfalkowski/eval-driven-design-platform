.PHONY: test build up down e2e

test:
	cd api && uv run pytest -q
	cd console && uv run pytest -q

build:
	./scripts/build_images.sh

up:
	cd deploy && docker compose up --build -d

down:
	./scripts/local_e2e.sh --stop

e2e:
	./scripts/local_e2e.sh
