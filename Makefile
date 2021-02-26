.PHONY: build build-dev up up-no-daemon tests attach shell help list static push publish

help: ## This help
	@grep -F "##" $(MAKEFILE_LIST) | grep -vF '@grep -F "##" $$(MAKEFILE_LIST)' | sed -r 's/(:).*##/\1/' | sort

list: ## List all targets
	@make -qp | awk -F':' '/^[a-zA-Z0-9][^$$#\/\t=]*:([^=]|$$)/ {split($$1,A,/ /);for(i in A)print A[i]}'

build: ## Build prod-like container
	docker build --tag=kyokley/mediaviewer --target=prod .

build-dev: ## Build dev container
	docker build --tag=kyokley/mediaviewer --target=dev .

up: ## Bring up containers and daemonize
	docker-compose up -d

up-no-daemon: ## Bring up all containers
	docker-compose up

attach: ## Attach to a running mediaviewer container
	docker attach $$(docker ps -qf name=mediaviewer_mediaviewer)

live-shell: up ## Open a shell in a mediaviewer container
	docker-compose exec mediaviewer /bin/bash

shell: ## Open a shell in a mediaviewer container
	docker-compose run mediaviewer /bin/bash

db-shell: up ## Open a shell in a mediaviewer container
	docker-compose exec postgres /bin/bash

tests: build-dev up ## Run tests
	./run-tests.sh

stop-all-but-db: ## Bring all containers down except postgres
	docker-compose down
	docker-compose up -d postgres

down: ## Bring all containers down
	docker-compose down

static: ## Install static files
	yarn install

push: build ## Push image to docker hub
	docker push kyokley/mediaviewer

publish: push ## Alias for push
