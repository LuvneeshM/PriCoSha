#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import datetime
import time

app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
	return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s and password = md5(%s)'
	cursor.execute(query, (username, password))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	firstname = request.form['firstname']
	lastname = request.form['lastname']

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if(data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO person VALUES(%s, md5(%s), %s, %s)'
		cursor.execute(ins, (username, password, firstname, lastname))
		conn.commit()

		colorMode = "INSERT INTO NightMode VALUES('{}',{})".format(username, 0)
		cursor.execute(colorMode)
		conn.commit()

		cursor.close()
		return render_template('index.html')

# ################################################################
# home page material
# ################################################################
@app.route('/home')
def home():
	username = session['username']
	cursor = conn.cursor();
	#query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
	#query = 'SELECT username, timest, content_name FROM Content WHERE (username = %s OR public = 1) ORDER BY timest DESC'
	query = "SELECT Content.id, Content.timest as post_timest, Content.username as post_username, content_name, file_path, GROUP_CONCAT(DISTINCT(SELECT CONCAT(first_name,' ',last_name) as name FROM Person WHERE Tag.username_taggee = Person.username AND status = 1)) as tagged, GROUP_CONCAT(DISTINCT CONCAT(Comment.username, ' ', Comment.timest, ' ', Comment.comment_text)) as comment FROM Content LEFT JOIN Tag on Content.id = Tag.id LEFT JOIN Comment ON Comment.id = Content.id WHERE (public = 1 OR (%s IN (SELECT username FROM member WHERE (member.group_name IN ( SELECT posterMember.group_name FROM member as posterMember WHERE posterMember.username= Content.username))) AND Content.id IN ( SELECT id FROM Share WHERE group_name IN ( SELECT group_name FROM Member WHERE username = %s)))) GROUP BY Content.id"
	cursor.execute(query, (username, username))
	data = cursor.fetchall()

	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	cursor.close()
	return render_template('home.html', username=username, posts=data, colors=colorMode)

# ################################################################
# Manage and see tags
# ################################################################
@app.route('/managetags/<int:content_id>/<string:option>/<string:taggee>/<string:tagger>', methods=['GET', 'POST'])
def manageTags(content_id, option, taggee, tagger):
	username = session['username']

	cursor = conn.cursor();

	if option == 'accept':
		query = "UPDATE Tag SET status = 1 WHERE id = {} AND username_taggee = '{}' AND username_tagger = '{}'".format(content_id, taggee, tagger)
		print("THIS IS ME!", query)
		cursor.execute(query)
	if option == 'decline':
		query = "DELETE FROM Tag WHERE id = {} AND username_taggee = '{}' AND username_tagger = '{}'".format(content_id, taggee, tagger)
		cursor.execute(query)

	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	query = "SELECT Content.content_name, Content.id, username_taggee, username_tagger FROM Content JOIN Tag ON Content.id = Tag.id WHERE status = 0 AND username_taggee = %s"
	cursor.execute(query, (username))
	data = cursor.fetchall()
	conn.commit()
	cursor.close()
	return render_template('tags.html', username=username, tags=data, colors=colorMode)

# ################################################################
# for posting
# ################################################################
@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	query = "SELECT group_name FROM FriendGroup WHERE username = %s"
	cursor.execute(query, (username))
	data = cursor.fetchall()

	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	cursor.close()
	return render_template('post.html', username=username, friends=data,colors=colorMode)
@app.route('/makePost', methods=['GET','POST'])
def makePost():
	username  = session['username']
	amIPublic = request.form.get('public')
	cursor = conn.cursor();
	query = None
	#update the content table
	if request.form.get('path') != "":
		print("PATH FULL")
		query = "INSERT INTO Content (username, timest, file_path, content_name, public) VALUES('{}','{}','{}','{}',{})".format(username, str(time.strftime('%Y-%m-%d %H:%M:%S')), str(request.form.get('path')), str(request.form.get('title')), (1 if amIPublic != None else 0) )
	else:
		print("PATH EMPTY")
		title_c = request.form.get('title')
		query = "INSERT INTO Content (username, timest, content_name, public) VALUES('{}','{}','{}',{})".format(username, str(time.strftime('%Y-%m-%d %H:%M:%S')), title_c, (1 if amIPublic != None else 0) )
	cursor.execute(query)
	data = cursor.fetchall()
	conn.commit()

	#person only likes private things
	if amIPublic == None:
			
		print("urg",request.form.getlist('friend_group_list'))

		for fr in request.form.getlist('friend_group_list'):
			print("I SHALL BE NOT PUBLIC")
			print("fr is", fr)
			query_2 = "SELECT max(tb.id) as maxId FROM (SELECT username, max(id) as id FROM Content Group By username) as tb WHERE tb.username=%s"
			cursor.execute(query_2, (username))
			data = cursor.fetchall()
			insertContent = "INSERT INTO Share VALUES({},'{}','{}')".format(data[0]['maxId'], str(fr) ,username)
			cursor.execute(insertContent)
			data = cursor.fetchall()
			conn.commit()

	cursor.close()
	return redirect(url_for('home'))

# ################################################################
# Tag someone else 
# ################################################################
@app.route('/tagging/<int:content_id>', methods=['GET', 'POST'])
def tagging(content_id):
	username = session['username']
	cursor = conn.cursor();
	# just get all the people to display on the page
	query = "SELECT username, first_name, last_name FROM Person"
	cursor.execute(query)
	data = cursor.fetchall()

	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	cursor.close()
	return render_template('tagging.html', username=username, id=content_id, persons=data,colors=colorMode)
@app.route('/taggingconfirm/<int:content_id>', methods=['GET', 'POST'])
def taggingConfirm(content_id):
	username = session['username']
	cursor = conn.cursor();
	#returns the user name as a list
	person = request.form.get('to_tag_person')
	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()
	if person == username:
		try:
			query = "INSERT INTO Tag (id, username_tagger, username_taggee, timest, status) VALUES ({}, '{}', '{}', '{}', true)".format(content_id, username, username, str(time.strftime('%Y-%m-%d %H:%M:%S')))
			cursor.execute(query)
			conn.commit()
			status = "Successfully tagged!"
		except:
			status = "You already tagged this person"
			return render_template('taggingconfirm.html', username=username, confirmed=status,colors=colorMode)
	else:
		query = "SELECT id FROM Content WHERE public = 1 OR (%s IN (SELECT username FROM member WHERE (member.group_name IN ( SELECT posterMember.group_name FROM member as posterMember WHERE posterMember.username= Content.username))) AND Content.id IN ( SELECT id FROM Share WHERE group_name IN ( SELECT group_name FROM Member WHERE username = %s))) GROUP BY Content.id"
		cursor.execute(query,(person, person))
		data = cursor.fetchall()
		for group in data:
			try:
				if group['id'] == content_id:
					query = "INSERT INTO Tag (id, username_tagger, username_taggee, timest, status) VALUES ({}, '{}', '{}', '{}', false)".format(content_id, username, person, str(time.strftime('%Y-%m-%d %H:%M:%S')))
					cursor.execute(query)
					conn.commit()
					status = "Successfully tagged!"
					return render_template('taggingconfirm.html', username=username, confirmed=status, colors=colorMode)
			except:
				status = "You already tagged this person"
				return render_template('taggingconfirm.html', username=username, confirmed=status, colors=colorMode)
		status = "Failed to tag person, they cannot view that content."
		return render_template('taggingconfirm.html', username=username, confirmed=status, colors=colorMode)

	return render_template('taggingconfirm.html', username=username, confirmed=status, colors=colorMode)

# ################################################################
# lets not be lonely anymore
# ################################################################
@app.route('/addingfriend', methods=['GET', 'POST'])
def addingFriend():
	username = session['username']
	cursor = conn.cursor();
	# get all the friendgroups that user owns
	query = "SELECT group_name FROM FriendGroup WHERE username = '{}'".format(username)
	cursor.execute(query)
	data = cursor.fetchall()
	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	return render_template('addingfriend.html', username=username, groups=data, colors=colorMode)
@app.route('/addingconfirm', methods=['GET', 'POST'])
def addingConfirm():
	username = session['username']
	cursor = conn.cursor();
	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	group_name = request.form.get('to_choose_group')
	try:
		first_name = request.form.get('to_choose_person').split(' ')[0]
		last_name = request.form.get('to_choose_person').split(' ')[1]
	except:
		status = "This is not the proper format for a name."
		return render_template('addingconfirm.html', username=username, confirmed=status, colors=colorMode)
	
	# get all the people with that first and last name - *should* return only one username
	query = "SELECT username FROM Person WHERE username != '{}' AND first_name = '{}' AND last_name = '{}'".format(username, first_name, last_name)
	cursor.execute(query)
	info = cursor.fetchall()

	if (len(info) == 0):
		status = "Invalid: person does not exist or you tried to add yourself."
		return render_template('addingconfirm.html', username=username, confirmed=status, colors=colorMode)

	person = info[0]['username']
	# multiple people issue
	if (len(info) > 1):
		status = "Cannot add person - more than one person with that name exists."
		return render_template('addingconfirm.html', username=username, confirmed=status, colors=colorMode)
	else:
		# get all the groups that the person is a member of
		query = "SELECT group_name FROM Member WHERE username = '{}' AND username_creator = '{}'".format(person, username)
		cursor.execute(query)
		groups = cursor.fetchall()
		# is this person already in the group they're being added to?
		for group in groups:
			if group['group_name'] == group_name:
				status = "This person is already a member of this group!"
				return render_template('addingconfirm.html', username=username, confirmed=status, colors=colorMode)

	query = "INSERT INTO Member VALUES('{}', '{}', '{}')".format(person, group_name, username)
	cursor.execute(query)
	conn.commit()
	status = "Friend added to group!"
	return render_template('addingconfirm.html', username=username, confirmed=status, colors=colorMode)

@app.route('/creategroup', methods=['GET', 'POST'])
def createGroup():
	username = session['username']
	cursor = conn.cursor();
	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	return render_template('creategroup.html', username=username, colors=colorMode)

@app.route('/createconfirm', methods=['GET', 'POST'])
def createConfirm():
	username = session['username']
	cursor = conn.cursor();
	#what color type
	query = "SELECT night_mode FROM NightMode WHERE username = %s"
	cursor.execute(query, (username))
	colorMode = cursor.fetchall()

	group_name = request.form.get('to_make_group')
	group_description = request.form.get('group_description')

	query = "SELECT group_name, username FROM FriendGroup WHERE group_name = '{}' AND username = '{}'".format(group_name, username)
	cursor.execute(query)
	data = cursor.fetchall()

	# does this person already have a group by this name?
	if (len(data) > 0):
		status = "You already own a group with this name!"
		return render_template('createconfirm.html', username=username, confirmed=status, colors=colorMode)

	# group is now in FriendGroup
	query = "INSERT INTO FriendGroup VALUES('{}', '{}', '{}')".format(group_name, username, group_description)
	cursor.execute(query)
	# user is now a member of the group they just made
	query = "INSERT INTO Member VALUES('{}', '{}', '{}')".format(username, group_name, username)
	cursor.execute(query)

	conn.commit()

	status = "Successfully created group!"
	return render_template('createconfirm.html', username=username, confirmed=status, colors=colorMode)

# ################################################################
# Night Mode
# ################################################################
@app.route('/nightMode', methods=['GET', 'POST'])
def nightMode():
	username = session['username']
	print("hi",request.form)
	print ("invert is", request.form.get('invert'))
	cursor = conn.cursor();
	if(request.form.get('invert') == 'on'):
		query = "UPDATE NightMode SET night_mode = 1 WHERE username = %s"
		cursor.execute(query, (username))
		conn.commit()
	else:
		query = "UPDATE NightMode SET night_mode = 0 WHERE username = %s"
		cursor.execute(query, (username))
		conn.commit()

	cursor.close()
	return redirect(url_for('home'))

#log out
@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')
		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)



if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)