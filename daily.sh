#!/bin/bash

echo "Starting daily cleanup `date`"
psql -d autodl -f /home/yokley/workspace/djangoApp/mysite/daily.sql
echo "Ending daily cleanup `date`"
