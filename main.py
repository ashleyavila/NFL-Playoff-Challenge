from flask import Flask, render_template, request, Response, g
from functools import wraps
from flaskext.auth import Auth, AuthUser

app = Flask(__name__, static_folder="static", template_folder="static")
auth = Auth(app)

@app.before_request
def init_users():
	admin = AuthUser(username='admin')
	admin.set_and_encrypt_password('password')
	g.users = {'admin':admin}

@app.route("/")
def main():
	return render_template('login.html')


@app.route("/login", methods=['POST','GET'])
def login():
	error = None
	if request.method == 'POST':
		username = request.form['username']
		if username in g.users:
			if g.users[username].authenticate(request.form['password']):
				return render_template('index.html', username=username)
			return render_template('login.html',error="Wrong password")
		return render_template('login.html',error="Not a user")
	return render_template('login.html',error="Unknown error logging in")

@app.route("/submit", methods=['POST'])
def submit():
	print request.form
	return "submitted"



if __name__ == '__main__':
	app.secret_key = "super secret"
	app.debug = True
	app.run()
