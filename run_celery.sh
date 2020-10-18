#!/bin/bash

args=$1
args2=$2
concurrency=${args2:-2}

echo "args: $args"
echo "args2: $args2"

echo "update directory permission"
chmod -R a+w /cronus/

echo "add new user"
adduser -D cronus

if [[ ! $args ]];then
    echo "the args value should be 'task' or 'celery'"
elif [[ $args == "task" ]];then
    echo "**********start task worker**********"
    su -m cronus -c "celery -A cronus worker -Q task -l info -c $concurrency"
elif [[ $args == "beat" ]]; then
    echo "**********start beat**********"
    su -m cronus -c "celery -A cronus beat -l info -S django --pidfile=/tmp/celerybeat.pid"
elif [[ $args == "celery" ]];then
    echo "**********start celery worker**********"
    su -m cronus -c "celery -A cronus worker -Q celery -l info -c $concurrency --max-tasks-per-child 50"
else
    echo "start worker failed, the args value should be 'task' or 'celery'"
fi