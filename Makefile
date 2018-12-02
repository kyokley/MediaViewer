.PHONY: build build_dev up tests

build:
	docker-compose build --build-arg REQS=base mediaviewer

build_dev:
	docker-compose build --build-arg REQS=dev mediaviewer

up:
	docker-compose up

tests: build_dev
	docker-compose run --rm mediaviewer sh -c "./wait-for.sh postgres:5432 && /venv/bin/python manage.py test && /venv/bin/bandit -x mediaviewer/tests -r ."
