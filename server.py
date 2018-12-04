from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
import re
import bcrypt
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'KeepItSecretKeepItSafe'
mysql = connectToMySQL('wall')

# def hasNumbers(inputString):
#     return any(char.isdigit() for char in inputString)


@app.route('/')
def index():
    query = "SELECT * FROM users"
    users = mysql.query_db(query)
    return render_template('index.html', all_users=users)

@app.route('/login', methods = ['POST'])
def login():
    # print request.form
    errors = []

    if len(request.form['email']) < 1:
        errors.append("Email cannot be blank")
    elif not EMAIL_REGEX.match(request.form['email']):
        errors.append("Invalid Email Address")
    else:
        query = "SELECT * FROM users WHERE email = %(email)s"
        user = mysql.query_db(query, {'email': request.form['email'].lower()})
        if len(user) < 1:
            errors.append("Unknown email.")

    if len(request.form['password']) < 1:
        errors.append("Password cannot be blank")
    elif len(request.form['password']) < 8:
        errors.append('Password must be 8 characters or more')

    if len(errors) > 0:
        for error in errors:
            flash(error)
        return redirect('/')
    else:
        if bcrypt.checkpw(request.form['password'].encode(), user[0]['password'].encode()):
            session['user'] = user[0]['id'], user[0]['first_name']
            return redirect('/wall')
        else:
            flash('Wrong password')
    return redirect('/')


@app.route('/register', methods = ['POST'])
def register():
    # print request.form
    errors = []

    if len(request.form['first_name']) < 2:
        errors.append("First name must be at least two letters")
    # elif hasNumbers(request.form['first_name']) == True:
    #     errors.append("First name cannot contain numbers")
    elif not request.form['first_name'].isalpha():
        errors.append('First name cannot include numbers.')

    if len(request.form['last_name']) < 2:
        errors.append("Last name must be at least two letters")
    # elif hasNumbers(request.form['last_name']) == True:
    #     errors.append("Last name cannot contain numbers")
    elif not request.form['last_name'].isalpha():
        errors.append('Last name cannot include numbers.')

    if len(request.form['email']) < 1:
        errors.append("Email cannot be blank")
    elif not EMAIL_REGEX.match(request.form['email']):
        errors.append("Invalid Email Address")
    else:
        query = "SELECT * FROM users WHERE email = %(email)s"
        user = mysql.query_db(query, {'email':request.form['email'].lower()})
        if len(user) > 0:
            errors.append('Email already in use.')

    if len(request.form['password']) < 1:
        errors.append("Password cannot be blank")
    elif len(request.form['password']) < 8:
        errors.append("Password must be at least 8 characters")
    if len(request.form['pass2']) < 1:
        errors.append("Password confirmation cannot be blank")
    elif request.form['password'] != request.form['pass2']:
        errors.append("Passwords do not match")

    if len(errors) > 0:
        for error in errors:
            flash(error)
        return redirect('/')
    else:
        query = 'INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, NOW(), NOW())'
        # print query
        data = {
            'first_name' : request.form['first_name'],
            'last_name' : request.form['last_name'],
            'email' : request.form['email'].lower(),
            'password' : bcrypt.hashpw(request.form['password'].encode(), bcrypt.gensalt())
        }
        # print data
        user_id = mysql.query_db(query, data)
        # print user_id
        # flash('Successfully registered')
        user = mysql.query_db('SELECT * FROM users WHERE id = {}'.format(user_id))
        session['user'] = user_id, user[0]['first_name']
        # return render_template('wall.html')
        return redirect('/wall')


@app.route('/wall')
def wall():
    if 'user' not in session:
        flash('You must login or register first')
        return redirect('/')

    query = "SELECT CONCAT(users.first_name, ' ', users.last_name) AS full_name, messages.message, messages.id AS message_id, messages.created_at FROM users LEFT JOIN messages ON users.id = messages.user_id ORDER BY messages.created_at DESC;"
    message_list = mysql.query_db(query)
    # print message_list

    query = "SELECT users.first_name, users.last_name, comments.comment, comments.created_at, comments.message_id FROM comments JOIN users ON comments.user_id = users.id ORDER BY comments.created_at DESC;"
    # data = {
    #     'message_id' : request.form['message_id']
    # }
    comment_list = mysql.query_db(query)
    # print comment_list


    return render_template('wall.html', user = session['user'], message_list = message_list, comment_list = comment_list)


@app.route('/message', methods = ['POST'])
def message():
    query = "SELECT id FROM users WHERE id = %(id)s"
    data = {
        'id': session['user'][0]
    }
    session_user_id = mysql.query_db(query, data)[0]['id']

    query = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES (%(user_id)s, %(message)s, NOW(), NOW())"

    data = {
         'message' : request.form['message'],
         'user_id' : session_user_id
    }

    mysql.query_db(query, data)

    return redirect('/wall')


@app.route('/comment', methods = ['POST'])
def comment():

    query = "INSERT INTO comments (user_id, message_id, comment, created_at, updated_at) VALUES (%(user_id)s, %(message_id)s, %(comment)s, NOW(), NOW())"
    data = {
        'user_id' : session['user'][0],
        'message_id' : request.form['message_id'],
        'comment' : request.form['comment'],
    }

    mysql.query_db(query, data)

    return redirect('/wall')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



app.run(debug=True)
