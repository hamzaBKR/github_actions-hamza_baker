.PHONY: help build run test clean push

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker container"
	@echo "  make run      - Run scraper in container"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Remove containers and images"
	@echo "  make push     - Push to container registry"
	@echo "  make local    - Run scraper locally (without container)"

build:
	docker build -t web-scraper:latest .

run:
	docker-compose up

test:
	docker-compose run scraper pytest test_scraper.py -v

clean:
	docker-compose down -v
	docker rmi web-scraper:latest || true

push:
	docker tag web-scraper:latest ghcr.io/$(USER)/web-scraper:latest
	docker push ghcr.io/$(USER)/web-scraper:latest

local:
	pip install -r requirements.txt
	python scraper.py
