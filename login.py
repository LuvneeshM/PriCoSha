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
		cursor.close()
		return render_template('index.html')

@app.route('/home')
def home():
	username = session['username']
	cursor = conn.cursor();
	#query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
	#query = 'SELECT username, timest, content_name FROM Content WHERE (username = %s OR public = 1) ORDER BY timest DESC'
	query = "SELECT Content.id, Content.timest as post_timest, Content.username as post_username, content_name, GROUP_CONCAT(DISTINCT(SELECT CONCAT(first_name,' ',last_name) as name FROM Person WHERE Tag.username_taggee = Person.username AND status = 1)) as tagged, GROUP_CONCAT(DISTINCT CONCAT(Comment.username, ' ', Comment.timest, ' ', Comment.comment_text)) as comment FROM Content LEFT JOIN Tag on Content.id = Tag.id LEFT JOIN Comment ON Comment.id = Content.id WHERE (public = 1 OR (%s IN (SELECT username FROM member WHERE (member.group_name IN ( SELECT posterMember.group_name FROM member as posterMember WHERE posterMember.username= Content.username))) AND Content.id IN ( SELECT id FROM Share WHERE group_name IN ( SELECT group_name FROM Member WHERE username = %s)))) GROUP BY Content.id"
	cursor.execute(query, (username, username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data)

#Manage tags
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

	
	query = "SELECT Content.content_name, Content.id, username_taggee, username_tagger FROM Content JOIN Tag ON Content.id = Tag.id WHERE status = 0 AND username_taggee = %s"
	cursor.execute(query, (username))
	data = cursor.fetchall()
	conn.commit()
	cursor.close()
	print(data)
	return render_template('tags.html', username=username, tags=data)

@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	query = "SELECT group_name FROM FriendGroup WHERE username = %s"
	print (query)
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('post.html', username=username, friends=data)

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