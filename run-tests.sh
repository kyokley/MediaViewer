#!/bin/bash

docker-compose run --rm mediaviewer sh -c "/venv/bin/pytest && /venv/bin/bandit -x ./mediaviewer/tests -r ."
exitcode=$?
docker-compose down
exit $exitcode
