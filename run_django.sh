#!/bin/bash

args2=$2
concurrency=${args2:-2}

echo 'generate static file'
python3 manage.py collectstatic --noinput

echo 'move default.conf'
sudo mv -f default.conf /etc/nginx/conf.d/

echo 'run nginx'
sudo mkdir -p /run/nginx/
sudo nginx

echo "**********start celery worker**********"
# su -m cronus -c "celery -A cronus worker -Q celery -l info -c $concurrency --max-tasks-per-child 50 > logs/celery.log 2>&1 &"
celery -A cronus worker -Q celery -l info -c $concurrency --max-tasks-per-child 50 > logs/celery.log 2>&1 &

echo '**********start django web application**********'
# su -m cronus -c 'uwsgi --ini backend_uwsgi.ini'
uwsgi --ini backend_uwsgi.ini