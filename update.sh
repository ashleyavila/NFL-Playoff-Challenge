git stash
git pull
git stash pop
killall gunicorn
gunicorn main:app --error-logfile /var/log/gunicorn/error.log, --log-file /var/log/gunicorn/gunicorn.log &

