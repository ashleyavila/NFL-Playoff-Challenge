git stash
git pull
git stash apply
killall gunicorn
gunicorn main:app &

