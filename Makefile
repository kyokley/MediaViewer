.PHONY: build build_dev up tests attach shell

build:
	docker-compose build --build-arg REQS=base mediaviewer

build_dev:
	docker-compose build --build-arg REQS=dev mediaviewer

up:
	docker-compose up

attach:
	docker attach $$(docker ps -qf name=mediaviewer_mediaviewer)

shell:
	docker-compose exec mediaviewer /bin/sh

tests: build_dev
	./run-tests.sh
