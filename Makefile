.PHONY: build build_dev up tests

build:
	docker-compose build --build-arg REQS=base mediaviewer

build_dev:
	docker-compose build --build-arg REQS=dev mediaviewer

up:
	docker-compose up

attach:
	docker attach

tests: build_dev
	./run-tests.sh
