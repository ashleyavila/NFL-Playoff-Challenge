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
import logging
logging.basicConfig(filename='nfl.log',level=logging.DEBUG)

CORRECTPICKS = {1: {1:2, 2:2, 3:2, 4:2}, 2: {1:1, 2:0, 3:1, 4:0}, 3: {1:0, 2:0}, 4: {1:0}} #The actual outcomes of games

TEAMS = ["Oakland Raiders", "Houston Texans", "Miami Dolphins", "Pittsburgh Steelers", "Detroit Lions", "Seattle Seahawks", "New York Giants", "Green Bay Packers", "New England Patriots", "Kansas City Chiefs", "Atlanta Falcons", "Dallas Cowboys"]
TIMES = {
1:{
1:{"team1":TEAMS[0],"team2":TEAMS[1],"time":"1/7/17 4:35PM"}, 
2:{"team1":TEAMS[2],"team2":TEAMS[3],"time":"1/8/17 1:05PM"}, 
3:{"team1":TEAMS[4],"team2":TEAMS[5],"time":"1/7/17 8:15PM"},
4:{"team1":TEAMS[6],"team2":TEAMS[7],"time":"1/8/17 4:40PM"}},
2:{
1:{"team1":TEAMS[8],"team2":TEAMS[1],"time":"1/14/17 8:15PM"}, 
2:{"team1":TEAMS[9],"team2":TEAMS[3],"time":"1/15/17 8:20PM"}, 
3:{"team1":TEAMS[10],"team2":TEAMS[5],"time":"1/14/17 4:35PM"},
4:{"team1":TEAMS[11],"team2":TEAMS[7],"time":"1/15/17 4:40PM"}},
3:{
1:{"team1":TEAMS[8],"team2":"","time":"1/22/17 6:40PM"}, 
2:{"team1":TEAMS[10],"team2":"","time":"1/22/17 3:05PM"}},
4:{
1:{"team1":"","team2":"", "time":"2/5/17 6:30PM"}}} #Times of kickoffs

TIEBREAK_USERNAMES = [] #Usernames that should get a .1 boost for tiebreaking

class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
    DEBUG = 				  os.getenv('DEBUG', 			True)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
    CSRF_ENABLED = True
    PREFIX = "/nflplayoffchallenge" #Set a url prefix (bar) to run at foo.com/bar

    # Flask-User settings
    USER_APP_NAME        = "NFL Playoff Challenge"
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
    hasBoughtIn = db.Column(db.Boolean(), nullable=False, server_default='0')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')
    picks = db.Column(db.String(100), nullable=True)
    tiebreaker = db.Column(db.String(100), nullable=True)
    
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    # group = db.Column(db.String(100), nullable=True, server_default='')
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

class PickForm(Form):
	picks = StringField('picks', validators=[validators.DataRequired("An error occurred")])
	tiebreaker = StringField('tiebreaker')
	submit = SubmitField('Save')

class GroupRegisterForm(forms.RegisterForm):
	print
	# group = StringField('Group', validators=[validators.DataRequired("A group name is required")])

db.create_all() # Create all database tables
# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app, register_form=GroupRegisterForm)     # Initialize Flask-User

@app.route("/")
def main():
	return redirect('/user/sign-in')


@app.route("/login", methods=['POST','GET'])
@login_required
def login():
	tiebreaker = ast.literal_eval(current_user.tiebreaker) if current_user.tiebreaker else {}
	return render_template('index.html', hasBoughtIn = current_user.hasBoughtIn, picks=convertPicks(current_user.picks), username=current_user.username,correctpicks=str(json.dumps(CORRECTPICKS)),times=getCurrentTimes(), tiebreaker=str(json.dumps(tiebreaker)))


@app.route("/submit", methods=['POST'])
@login_required
def submit():
	form = PickForm(request.form, current_user)
	if request.method == 'POST':
		print form.picks.data
		print form.tiebreaker.data
		valid = validatePicks(form.picks.data)
		if valid[0] and time.strptime(TIMES[4][1]["time"], "%m/%d/%y %I:%M%p") >= time.localtime():
			current_user.picks = cleanForm(form.picks.data, current_user.picks)
			current_user.tiebreaker = str(form.tiebreaker.data)
			db.session.commit()
			return render_template('index.html', hasBoughtIn = current_user.hasBoughtIn, picks=convertPicks(current_user.picks), username=current_user.username, submission="Successfully submitted",correctpicks=str(json.dumps(CORRECTPICKS)),times=getCurrentTimes(), tiebreaker=str(json.dumps(ast.literal_eval(current_user.tiebreaker))))
		logging.info("Failed to save picks for " + current_user.username + ": " + form.picks.data)
		return render_template('index.html', hasBoughtIn = current_user.hasBoughtIn, picks=convertPicks(current_user.picks), username=current_user.username, submission="Picks were not valid",correctpicks=str(json.dumps(CORRECTPICKS)),times=getCurrentTimes(), tiebreaker=str(json.dumps(ast.literal_eval(current_user.tiebreaker if current_user.tiebreaker else "{}"))))

@app.route("/leaderboard", methods=['GET'])
@login_required
def leaderboard():
	leaderboard = getLeaderboard("current_user.group")
	return render_template('leaderboard.html', group="current_user.group", data=leaderboard)

def getCurrentTimes():
	times = TIMES
	for i in TIMES:
		for j in TIMES[i]:
			gameTime = time.strptime(TIMES[i][j]["time"], "%m/%d/%y %I:%M%p")
			if gameTime < time.localtime():
				TIMES[i][j]["locked"] = True
			else:
				TIMES[i][j]["locked"] = False
	return TIMES

def getLeaderboard(group):
	leaderboard = {}
	# users = User.query.filter(User.group == group).all()
	users = User.query.all()

	for user in users:
		tieb = 0
		if (user.tiebreaker is not None) and user.tiebreaker != "{}":
			tieb = str(str(ast.literal_eval(user.tiebreaker)["1"])+":"+str(ast.literal_eval(user.tiebreaker)["2"])) if user.tiebreaker else ""
			if tieb and time.strptime(TIMES[4][1]["time"], "%m/%d/%y %I:%M%p") >= time.localtime():
				tieb = "?:?"

		score = calculateScore(user.picks)
		if user.username in TIEBREAK_USERNAMES:
			score = score + .1
		leaderboard[user.username] = [score, calculatePossible(user.picks)] + getPastPicks(user.picks) + [tieb]
	return leaderboard

def getPastPicks(picks):
	itera = {1: {1:0,2:0,3:0,4:0}, 2: {1:0,2:0,3:0,4:0}, 3: {1:0,2:0}, 4: {1:0}}
	pastPicks = []
	if type(picks) is unicode:
		picks = ast.literal_eval(picks)
	if not picks:
		picks = {1: {}, 2: {}, 3: {}, 4: {}}
	for week in itera.keys():
		for game in itera[week].keys():
			if game in picks[week].keys():
				gameTime = time.strptime(TIMES[week][game]["time"], "%m/%d/%y %I:%M%p")
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
	return pastPicks


def calculateScore(picks):
	if type(picks) is unicode:
		picks = ast.literal_eval(picks)
	if not picks:
		return 0
	score = 0
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
	for p in picks.keys():
		for r in picks[p].keys():
			if r in CORRECTPICKS[p] and CORRECTPICKS[p][r] !=0 and CORRECTPICKS[p][r] != picks[p][r][0]:
				score -= picks[p][r][1]
	return score

def validatePicks(picks):
	picks = ast.literal_eval(picks)
	
	used = []
	for pick in picks.keys():
		week = int(pick[4])
		game = int(pick[6])	
		points = int(picks[pick])
		if points in used and points != 0:
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
		gameTime = time.strptime(TIMES[week][game]["time"], "%m/%d/%y %I:%M%p")
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
