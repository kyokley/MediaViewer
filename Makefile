.PHONY: build build-dev up up-no-daemon tests attach shell help list static

help: ## This help
	@grep -F "##" $(MAKEFILE_LIST) | grep -vF '@grep -F "##" $$(MAKEFILE_LIST)' | sed -r 's/(:).*##/\1/' | sort

list: ## List all targets
	@make -qp | awk -F':' '/^[a-zA-Z0-9][^$$#\/\t=]*:([^=]|$$)/ {split($$1,A,/ /);for(i in A)print A[i]}'

build:
	docker-compose build mediaviewer

build-dev:
	docker-compose build --build-arg REQS= mediaviewer

up:
	docker-compose up -d

up-no-daemon:
	docker-compose up

attach:
	docker attach $$(docker ps -qf name=mediaviewer_mediaviewer)

shell: up
	docker-compose run --rm mediaviewer /bin/bash

tests: build-dev
	./run-tests.sh

stop-all-but-db:
	docker-compose down
	docker-compose up -d postgres

down:
	docker-compose down

static:
	yarn install
