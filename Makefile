.PHONY: build up test clean test-env-up test-env-down coverage

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

test-env-up:
	docker compose -f docker-compose_test.yaml up -d --build
	# Wait a bit for services to initialize
	sleep 15

test-env-down:
	docker compose -f docker-compose_test.yaml down

coverage: test-env-up
	docker compose -f docker-compose_test.yaml exec app pytest --cov=avauth_proxy --cov-report term-missing
	$(MAKE) test-env-down

test: test-env-up
	docker compose -f docker-compose_test.yaml exec app pytest
	$(MAKE) test-env-down

clean:
	docker compose down
	rm -rf logs/
