.PHONY: build build-dev up up-no-daemon tests attach shell help list static push publish

UID := 1000

export UID

DOCKER_COMPOSE_EXECUTABLE=$$(which docker-compose >/dev/null 2>&1 && echo 'docker-compose' || echo 'docker compose')

help: ## This help
	@grep -F "##" $(MAKEFILE_LIST) | grep -vF '@grep -F "##" $$(MAKEFILE_LIST)' | sed -r 's/(:).*##/\1/' | sort

list: ## List all targets
	@make -qp | awk -F':' '/^[a-zA-Z0-9][^$$#\/\t=]*:([^=]|$$)/ {split($$1,A,/ /);for(i in A)print A[i]}'

build: touch-history ## Build prod-like container
	docker build --build-arg UID=${UID} --tag=kyokley/mediaviewer --target=prod .

build-dev: touch-history ## Build dev container
	docker build --build-arg UID=${UID} --tag=kyokley/mediaviewer --target=dev .

up: touch-history ## Bring up containers and daemonize
	${DOCKER_COMPOSE_EXECUTABLE} up -d

up-no-daemon: touch-history ## Bring up all containers
	${DOCKER_COMPOSE_EXECUTABLE} up

attach: touch-history ## Attach to a running mediaviewer container
	docker attach $$(docker ps -qf name=mediaviewer_mediaviewer)

live-shell: up ## Open a shell in a mediaviewer container
	${DOCKER_COMPOSE_EXECUTABLE} exec mediaviewer /bin/bash

shell: touch-history ## Open a shell in a mediaviewer container
	${DOCKER_COMPOSE_EXECUTABLE} run mediaviewer /bin/bash

db-shell: up ## Open a shell in a mediaviewer container
	${DOCKER_COMPOSE_EXECUTABLE} exec postgres /bin/bash

pytest: build-dev up ## Run tests
	${DOCKER_COMPOSE_EXECUTABLE} run --rm mediaviewer /venv/bin/pytest -n 4

bandit: build-dev ## Run bandit tests
	${DOCKER_COMPOSE_EXECUTABLE} run --rm --no-deps mediaviewer /venv/bin/bandit -x ./mediaviewer/tests,./.venv -r .

check-migrations: build-dev ## Check for missing migrations
	${DOCKER_COMPOSE_EXECUTABLE} run --rm mediaviewer /venv/bin/python manage.py makemigrations --check

tests: check-migrations pytest bandit ## Run all tests

stop-all-but-db: ## Bring all containers down except postgres
	${DOCKER_COMPOSE_EXECUTABLE} down
	${DOCKER_COMPOSE_EXECUTABLE} up -d postgres

down: ## Bring all containers down
	${DOCKER_COMPOSE_EXECUTABLE} down --remove-orphans

static: ## Install static files
	yarn install

push: build ## Push image to docker hub
	docker push kyokley/mediaviewer

publish: push ## Alias for push

autoformat:
	${DOCKER_COMPOSE_EXECUTABLE} run --rm --no-deps mediaviewer /venv/bin/black .
	${DOCKER_COMPOSE_EXECUTABLE} run --rm --no-deps mediaviewer /venv/bin/isort .

touch-history:
	@touch .mv.history
	@mkdir -p logs
	@chmod 777 -R logs
