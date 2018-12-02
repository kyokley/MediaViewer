#!/bin/bash

docker-compose run --rm mediaviewer sh -c "./wait-for.sh postgres:5432 && /venv/bin/python manage.py test && /venv/bin/bandit -x mediaviewer/tests -r ."
exitcode=$?
docker-compose down
exit $exitcode
