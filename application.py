from flask import Flask, render_template, make_response, request, jsonify, url_for, flash, redirect
app = Flask(__name__)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, User, Quote
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

CLIENT_ID = json.loads(open('client-secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///quotecamp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def HomePage():
    return render_template('main.html')

@app.route('/login')
def LoginPage():
    state = ''.join(random.choice(string.ascii_letters + string.digits)
        for x in range(32))
    login_session['state'] = state
    
    # Show the login auth page
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
        response = make_response(json.dumps('Failed to upgrade the auth code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    
    # Create a JSON get request with access token and the url, stored in result
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if(result.get('error') is not None):
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    
    # Check that the access tokens match 
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(json.dumps("Token user id does not match given user id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token client id does not match given client id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Check if the user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_google_id = login_session.get('google_id')
    if stored_credentials is not None and google_id == stored_google_id:
        response = make_response(json.dumps("User is logged in"), 200)
        response.headers['Content-Type'] = 'application/json'
    login_session['credentials'] = credentials
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

    # see if a user exists. If not, make one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
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
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Check with Google's Servers to to disconnect user from them.
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['credentials']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('User successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for the user.'), 400)
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

@app.route('/categories/<category_name>/')
@app.route('/categories/category/')
def CategoryPage():
    # Get all the quotes under the specified category
    return render_template('category.html')

@app.route('/categories/category/quote')
@app.route('/categories/<category_name>/<int:quote_id>')
def QuotePage():
    # Get the specifics of the quote page
    return render_template('quoteview.html')

@app.route('/categories/newquote/')
def NewQuotePage():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    return render_template('newquote.html', categories=categories)

@app.route('/categories/<category_name>/<int:quote_id>/edit')
def EditQuotePage():
    # Edit a quote if you are the user that creates/manages that quote
    return "Edit Quote Page"

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)