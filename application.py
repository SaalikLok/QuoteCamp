import random
import string
import sys
import httplib2
import json
import requests
import datetime
from flask import (Flask, render_template, make_response,
                   request, jsonify, url_for, flash, redirect)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, User, Quote
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
app = Flask(__name__)


CLIENT_ID = json.loads(open('client-secrets.json', 'r')
                       .read())['web']['client_id']

engine = create_engine('sqlite:///quotecamp.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
def HomePage():
    latestquotes = session.query(Quote).order_by(
        Quote.datetime_added.desc()).all()
    return render_template('main.html', latestquotes=latestquotes)


@app.route('/login')
def LoginPage():
    state = ''.join(random.choice(string.ascii_letters + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # Show the login auth page,
    # passing with it the state variable of the random string
    return render_template('login.html', STATE=state)
    # return "Current State Token: " + login_session['state']


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # confirm that token sent to client is same as token sent to server
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # collect the code from the server, exchange it for a credentials object
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client-secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the auth code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)

    # Create a JSON get request with access token and the url, stored in result
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if(result.get('error') is not None):
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access tokens match
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(json.dumps(
            "Token user id does not match given user id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token client id does not match given client id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if the user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(json.dumps(
            "User is logged in and connected"), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info according to the token's scope
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Store user data in the login session
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if a user exists. If not, make one
    user_id = getUserID(data['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += str(login_session['user_id'])
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Disconnect an already connected user
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check with Google's Servers to to disconnect user from them.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps(
            'User successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for the user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnnect/')
def disconnect():
    if 'provider' in login_session:
        gdisconnect()
        del login_session['google_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfully logged out.")
        return redirect(url_for('HomePage'))
    else:
        flash("You were not logged in")
        return redirect(url_for('HomePage'))


@app.route('/categories/')
def CategoriesPage():
    # List all the categories in the app on a page.
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)


@app.route('/categories/<category_id>/')
@app.route('/categories/category/')
def CategoryPage(category_id):
    # Get all the quotes under the specified category
    category = session.query(Category).filter_by(id=category_id).one()
    quotes = session.query(Quote).filter_by(category_id=category_id).all()
    return render_template('category.html', quotes=quotes, category=category)


@app.route('/categories/<category_id>/<int:quote_id>')
def QuotePage(quote_id, category_id):
    # Get the specifics of the quote page
    quote = session.query(Quote).filter_by(id=quote_id).one()
    creator = session.query(User).filter_by(id=quote.poster_id).one()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('quoteviewpublic.html', quote=quote, creator=creator)
    else:
        return render_template('quoteview.html', quote=quote, creator=creator)


@app.route('/categories/newquote/', methods=['GET', 'POST'])
def NewQuotePage():
    if 'username' not in login_session:
        return redirect('/login')
    creator = getUserID(login_session['email'])
    if request.method == 'POST':
        NewQuotePage = Quote(
            content=request.form['quote'],
            author=request.form['author'],
            poster_id=creator,
            category_id=request.form['category'],
            datetime_added=datetime.datetime.now(),)
        session.add(NewQuotePage)
        session.commit()
        return redirect(url_for('HomePage'))
    else:
        categories = session.query(Category).all()
        return render_template('newquote.html', categories=categories)


@app.route('/categories/<category_id>/<int:quote_id>/edit', methods=['GET', 'POST'])
def EditQuotePage(quote_id, category_id):
    editedQuote = session.query(Quote).filter_by(id=quote_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedQuote.poster_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You can't edit this quote, you didn't post it.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['quote']:
            editedQuote.content = request.form['quote']
        if request.form['author']:
            editedQuote.author = request.form['author']
        if request.form['category']:
            editedQuote.category_id = request.form['category']
        return redirect(url_for('CategoryPage', category_id=editedQuote.category_id))
    else:
        categories = session.query(Category).all()
        return render_template('editquote.html', quote=editedQuote, categories=categories)


@app.route('/categories/<category_id>/<int:quote_id>/delete', methods=['GET', 'POST'])
def DeleteQuote(quote_id, category_id):
    quoteToDelete = session.query(Quote).filter_by(id=quote_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if quoteToDelete.poster_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You can't delete this quote, you didn'tpost it.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(quoteToDelete)
        session.commit()
        return redirect(url_for('CategoryPage', category_id=category.id))
    else:
        return render_template('deletequote.html', quote=quoteToDelete)


# JSON Endpoint of entire site
@app.route('/JSON')
def allQuotesJSON():
    quotes = session.query(Quote).all()
    return jsonify(quotes=[q.serialize for q in quotes])


# JSON list of quotes within a category
@app.route('/categories/<category_id>/JSON')
def quotesInCategoryJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    quotes = session.query(Quote).filter_by(category_id=category.id).all()
    return jsonify(quotes=[q.serialize for q in quotes])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
