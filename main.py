from flask import * 
from flask_mail import Mail
from flask_login import *
from flask_wtf import *
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask_user import *
import os
import ast
from flask_wtf import Form
from wtforms import StringField, SubmitField, validators

class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
    DEBUG = 				  os.getenv('DEBUG', 			True)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
    CSRF_ENABLED = True

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'nflplayoffchallenge@samgiagtzoglou.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        '')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"NFL Playoff Challenge" <nflplayoffchallenge@samgiagtzoglou.com>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'personal.samgiagtzoglou.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '25'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         False))

    # Flask-User settings
    USER_APP_NAME        = "AppName"                # Used by email templates
    USER_ENABLE_EMAIL              = os.getenv('USER_ENABLE_EMAIL', False)
    USER_AFTER_LOGIN_ENDPOINT = 'login'
    USER_AFTER_LOGOUT_ENDPOINT = ''

app = Flask(__name__, static_folder="static", template_folder="static")
app.config.from_object(__name__+'.ConfigClass')
db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')
    picks = db.Column(db.String(100), nullable=True)
    
    # User email information
    # email = db.Column(db.String(255), nullable=False, unique=True)
    # confirmed_at = db.Column(db.DateTime())

    # User information
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

class PickForm(Form):
	picks = StringField('picks', validators=[validators.DataRequired("An error occurred")])
	submit = SubmitField('Save')

# Create all database tables
db.create_all()
# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

# @app.before_request
# def init_users():
# 	admin = AuthUser(username='admin')
# 	admin.set_and_encrypt_password('password')
# 	g.users = {'admin':admin}

@app.route("/")
def main():
	return redirect('/user/sign-in')
	# return render_template('login.html')


@app.route("/login", methods=['POST','GET'])
@login_required
def login():
	# return render_template('index.html', username=username)

	# error = None
	# if request.method == 'POST':
	# 	username = request.form['username']
	# 	if username in g.users:
	# 		if g.users[username].authenticate(request.form['password']):
	return render_template('index.html', picks=convertPicks(current_user.picks), username=current_user.username)
	# 		return render_template('login.html',error="Wrong password")
	# 	return render_template('login.html',error="Not a user")
	# return render_template('login.html',error="Unknown error logging in")


@app.route("/submit", methods=['POST'])
@login_required
def submit():
	form = PickForm(request.form, current_user)
	if request.method == 'POST':
		print 'tried'
		current_user.picks = cleanForm(form.picks.data)
		# form.populate_obj(current_user)
		db.session.commit()
		# picks = ast.literal_eval(request.form['picks'])
		# s = {1:{},2:{},3:{},4:{},}
		# for pick in picks.keys():
		# 	print pick
		# 	week = int(pick[4])
		# 	game = int(pick[6])
		# 	team = int(pick[8])
		# 	points = int(picks[pick])
		# 	print str(week), ' ',  game,  ' ',  team,  ' ',  points
		# 	if points > 0:
		# 		s[week][game] = [team, points]
		# print s
		# request
	return render_template('index.html', picks=convertPicks(current_user.picks), username=current_user.username, submission="Successfully submitted")

def cleanForm(i):
	print i
	picks = ast.literal_eval(i)
	s = {1:{},2:{},3:{},4:{},}
	for pick in picks.keys():
		print pick
		week = int(pick[4])
		game = int(pick[6])
		team = int(pick[8])
		points = int(picks[pick])
		print str(week), ' ',  game,  ' ',  team,  ' ',  points
		if points > 0:
			s[week][game] = [team, points]
	return str(s)

def convertPicks(old):
	print old
	old = ast.literal_eval(old)
	new = {}
	for p in old.keys():
		for r in old[p].keys():
			s = old[p][r]
			new["game"+str(p)+"-"+str(r)+"-"+str(s[0])] = s[1]
	print new
	return str(new).replace('\'','\"')


if __name__ == '__main__':
	app.debug = True
	app.run()
