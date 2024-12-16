.PHONY: build up test clean

build:
	docker-compose build

up:
	docker-compose up

test:
	python run_tests.py

clean:
	docker-compose down
	rm -rf logs/
