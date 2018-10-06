from flask import Flask, render_template, request, redirect, url_for, logging, session, flash
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from functools import wraps
from database import dbusers

app = Flask(__name__)
app.debug=True

db_users = dbusers() # Hiding database info from others

# Config MySQL
app.config['MYSQL_HOST'] = db_users['host']
app.config['MYSQL_USER'] = db_users['user']
app.config['MYSQL_PASSWORD'] = db_users['password']
app.config['MYSQL_DB'] = db_users['db']
app.config['MYSQL_CURSORCLASS'] = db_users['cursor']

app.secret_key = 'verySecret#123'

# Init MySQL
mysql = MySQL(app)


# Home route
@app.route('/')
def home():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    cur.close()

    if result > 0:
        return render_template('home.html', articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('home.html')

#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

# About Route/Page
@app.route('/about')
def about():
    return render_template('about.html')

#Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Successful. You are registered. You may login.', 'success')

        return redirect(url_for('login', _external=True))
    return render_template('register.html', form=form)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute SQL
        result = cur.execute('SELECT * FROM users WHERE username= %s', [username])
        # print(data['user'])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            print(data['password'])
            # Compare Password
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username
                print(session['logged_in'])

                flash('You are logged in.', 'success')
                # return render_template('about.html')

                return redirect(url_for('dashboard', _external=True))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user looged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized! Please login.', 'danger')
            return redirect(url_for('login'))
    return wrap

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    cur.close()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    content = TextAreaField('Content', [validators.Length(min=30)])

# Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, content, author) VALUES(%s, %s, %s)", (title, content, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Successful! Article has been added', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
     # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.content.data = article['content']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        content = request.form['content']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, content=%s WHERE id=%s",(title, content, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Logout Route
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You successfully logged out', 'success')
    # return render_template('login.html')
    return redirect(url_for('login'))

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()
    print("Deteting post " + id)
    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run()
