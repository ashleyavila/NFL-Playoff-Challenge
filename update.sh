git pull
killall gunicorn
gunicorn main:app --error-logfile /var/log/gunicorn/error.log, --log-file /var/log/gunicorn/gunicorn.log &

