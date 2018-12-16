.PHONY: build build-dev up tests attach shell

build:
	docker-compose build --build-arg REQS=base mediaviewer

build-dev:
	docker-compose build --build-arg REQS=dev mediaviewer

up:
	docker-compose up -d

up-no-daemon:
	docker-compose up

attach:
	docker attach $$(docker ps -qf name=mediaviewer_mediaviewer)

shell: up
	docker-compose exec mediaviewer /bin/sh

tests: build-dev
	./run-tests.sh

stop-all-but-db:
	docker-compose down
	docker-compose up -d postgres

down:
	docker-compose down
