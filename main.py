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
import time
import operator
import json

TIMES = {1:{1:"1/4/15 1:05PM", 2:"1/3/15 8:15PM", 3:"1/3/15 4:35PM",4:"1/4/15 4:40PM"},2:{1:"1/11/15 4:40PM", 2:"1/10/15 4:35PM", 3:"1/10/15 8:15PM",4:"1/11/15 1:05PM"},3:{1:"1/18/15 6:40PM", 2:"1/18/15 3:05PM"},4:{1:"2/1/15 6:30PM"}}
CORRECTPICKS = {1: {1:1,2:2,3:1,4:1}, 2: {1:2,2:1,3:1,4:1}, 3: {1:2,2:1}, 4: {1:1}}

class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
    DEBUG = 				  os.getenv('DEBUG', 			True)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
    CSRF_ENABLED = True
    PREFIX = "/nflplayoffchallenge" #Set a url prefix (bar) to run at foo.com/bar

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'nflplayoffchallenge@samgiagtzoglou.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        '')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"NFL Playoff Challenge" <nflplayoffchallenge@samgiagtzoglou.com>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'personal.samgiagtzoglou.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '25'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         False))

    # Flask-User settings
    USER_APP_NAME        = "NFL Playoff Challenge"                # Used by email templates
    USER_ENABLE_EMAIL              = os.getenv('USER_ENABLE_EMAIL', False)
    USER_AFTER_LOGIN_ENDPOINT = 'login'
    USER_AFTER_LOGOUT_ENDPOINT = ''

app = Flask(__name__, static_folder="static", template_folder="static")
app.config.from_object(__name__+'.ConfigClass')

db = SQLAlchemy(app)
mail = Mail(app)
# g.runlocally = "/nflplayoffchallenge"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')
    picks = db.Column(db.String(100), nullable=True)
    tiebreaker = db.Column(db.String(100), nullable=True)
    # User email information
    # email = db.Column(db.String(255), nullable=False, unique=True)
    # confirmed_at = db.Column(db.DateTime())

    # User information
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    group = db.Column(db.String(100), nullable=False, server_default='')
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

class PickForm(Form):
	picks = StringField('picks', validators=[validators.DataRequired("An error occurred")])
	tiebreaker = StringField('tiebreaker')
	submit = SubmitField('Save')

class GroupRegisterForm(forms.RegisterForm):
	group = StringField('Group', validators=[validators.DataRequired("A group name is required")])

# Create all database tables
db.create_all()
# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app, register_form=GroupRegisterForm)     # Initialize Flask-User

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
	tiebreaker = ast.literal_eval(current_user.tiebreaker) if current_user.tiebreaker else {}

	return render_template('index.html', picks=convertPicks(current_user.picks), username=current_user.username,correctpicks=str(json.dumps(CORRECTPICKS)),times=TIMES, tiebreaker=str(json.dumps(tiebreaker)))
	# 		return render_template('login.html',error="Wrong password")
	# 	return render_template('login.html',error="Not a user")
	# return render_template('login.html',error="Unknown error logging in")


@app.route("/submit", methods=['POST'])
@login_required
def submit():
	form = PickForm(request.form, current_user)
	if request.method == 'POST':
		print form.picks.data
		print form.tiebreaker.data
		valid = validatePicks(form.picks.data)
		if valid[0] and time.strptime(TIMES[4][1], "%m/%d/%y %I:%M%p") >= time.localtime():
			current_user.picks = cleanForm(form.picks.data, current_user.picks)
			current_user.tiebreaker = str(form.tiebreaker.data)
			db.session.commit()
			return render_template('index.html', picks=convertPicks(current_user.picks), username=current_user.username, submission="Successfully submitted",correctpicks=str(json.dumps(CORRECTPICKS)),times=TIMES, tiebreaker=str(json.dumps(ast.literal_eval(current_user.tiebreaker))))
		return render_template('index.html', picks=convertPicks(current_user.picks), username=current_user.username, submission="Picks were not valid",correctpicks=str(json.dumps(CORRECTPICKS)),times=TIMES, tiebreaker=str(json.dumps(ast.literal_eval(current_user.tiebreaker))))

@app.route("/leaderboard", methods=['GET'])
@login_required
def leaderboard():
	leaderboard = getLeaderboard(current_user.group)
	return render_template('leaderboard.html', group=current_user.group, data=leaderboard)

def getLeaderboard(group):
	leaderboard = {}
	users = User.query.filter(User.group == group).all()
	print users
	# users2 = sorted(users, key=calculateScore(str(operator.itemgetter('picks'))))

	for user in users:
		if (user.tiebreaker is not None) and user.tiebreaker != "{}":
			print user.tiebreaker
			tieb = str(str(ast.literal_eval(user.tiebreaker)["1"])+":"+str(ast.literal_eval(user.tiebreaker)["2"])) if user.tiebreaker else ""
		if tieb and time.strptime(TIMES[4][1], "%m/%d/%y %I:%M%p") >= time.localtime():
			tieb = "?:?"
		leaderboard[user.username] = [calculateScore(user.picks), calculatePossible(user.picks)] + getPastPicks(user.picks) + [tieb]
	return leaderboard

def getPastPicks(picks):
	itera = {1: {1:0,2:0,3:0,4:0}, 2: {1:0,2:0,3:0,4:0}, 3: {1:0,2:0}, 4: {1:0}}
	pastPicks = []#{1: {}, 2: {}, 3: {}, 4: {}}
	if type(picks) is unicode:
		picks = ast.literal_eval(picks)
	if not picks:
		picks = {1: {}, 2: {}, 3: {}, 4: {}}
	for week in itera.keys():
		for game in itera[week].keys():
			# team = int(pick[8])
			if game in picks[week].keys():
				gameTime = time.strptime(TIMES[week][game], "%m/%d/%y %I:%M%p")
				if gameTime < time.localtime():
					if picks[week][game][0] == CORRECTPICKS[week][game]:
						pastPicks.append(picks[week][game][1])
					elif CORRECTPICKS[week][game] == 0:
						pastPicks.append(str(picks[week][game][0])+":("+str(picks[week][game][1])+")")
					else:
						pastPicks.append("("+str(picks[week][game][1])+")")
				else:
					pastPicks.append("?")
			else:
				pastPicks.append(" ")
					# pastPicks[week][game] = picks[week][game]
	return pastPicks


def calculateScore(picks):
	if type(picks) is unicode:
		picks = ast.literal_eval(picks)
	if not picks:
		return 0
	score = 0
	# picks = {1: {1:[2,5],2:[1,3],3:[2,2],4:[2,7]}, 2: {}, 3: {}, 4: {}}
	
	for p in picks.keys():
		for r in picks[p].keys():
			if r in CORRECTPICKS[p] and CORRECTPICKS[p][r] == picks[p][r][0]:
				score += picks[p][r][1]
	return score

def calculatePossible(picks):
	if type(picks) is unicode:
		picks = ast.literal_eval(picks)
	if not picks:
		return 0
	score = 66
	# picks = {1: {1:[2,5],2:[1,3],3:[2,2],4:[2,7]}, 2: {}, 3: {}, 4: {}}
	
	for p in picks.keys():
		for r in picks[p].keys():
			if r in CORRECTPICKS[p] and CORRECTPICKS[p][r] !=0 and CORRECTPICKS[p][r] != picks[p][r][0]:
				score -= picks[p][r][1]
	return score

def validatePicks(picks):
	picks = ast.literal_eval(picks)
	# picks = {1: {1:[2,5],2:[1,3],3:[2,2],4:[2,7]}, 2: {}, 3: {}, 4: {}}
	
	used = []
	for pick in picks.keys():
		week = int(pick[4])
		game = int(pick[6])	
		points = int(picks[pick])
		if points in used:
			return [False, "Used same point value more than once"]
		used.append(points)
	return [True]

def cleanForm(i,oldPicks):
	print i
	oldPicks = ast.literal_eval(oldPicks) if oldPicks else {1:{},2:{},3:{},4:{}}
	picks = ast.literal_eval(i)
	s = {1:{},2:{},3:{},4:{}}
	
	for pick in picks.keys():
		print pick
		week = int(pick[4])
		game = int(pick[6])
		team = int(pick[8])
		gameTime = time.strptime(TIMES[week][game], "%m/%d/%y %I:%M%p")
		points = int(picks[pick])
		print str(week), ' ',  game,  ' ',  team,  ' ',  points
		if points > 0:
			if gameTime >= time.localtime():
				s[week][game] = [team, points]
			else:
				s[week][game] = oldPicks[week][game] if game in oldPicks[week] else [0,0]
	return str(s)

def convertPicks(old):
	if not old:
		return "{}"
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
	app.run(port=8000)
