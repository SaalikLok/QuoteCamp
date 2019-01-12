from flask import Flask, render_template, make_response
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
@app.route('/hello')
def HelloWorld():
    return render_template('main.html')

@app.route('/login')
def LoginPage():
    state = ''.join(random.choice(string.ascii_letters + string.digits)
        for x in range(32))
    login_session['state'] = state
    
    # Show the login auth page
    return render_template('login.html')
    # return "Current State Token: " + login_session['state']

@app.route('/gconnect', methods=['POST'])
def Gconnect():
    if(request.args.get('state') != login_session['state']):
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if(result.get('error') is not None):
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(json.dumps("Token user id does not match given user id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token client id does not match given client id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('credentials')
    stored_google_id = login_session.get('google_id')
    if stored_credentials is not None and google_id == stored_google_id:
        response = make_response(json.dumps("User is logged in"), 200)
        response.headers['Content-Type'] = 'application/json'
    login_session['credentials'] = credentials
    login_session['google_id'] = google_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    #flash("you are now logged in as %s" % login_session['username'])
    return output

@app.route('/categories/')
def CategoriesPage():
    # List all the categories in the app on a page.
    categoryListFromDB = session.query(Category).all()
    output = ""
    for i in categoryListFromDB:
        output += (i.name + '<br/>')
    return output

@app.route('/categories/<category_name>/')
def CategoryPage():
    # Get all the quotes under the specified category
    return "Category Page"

@app.route('/categories/<category_name>/<int:quote_id>')
def QuotePage():
    # Get the specifics of the quote page
    return "Quote Page"

@app.route('/categories/<category_name>/new')
def NewQuotePage():
    # Template for creating a new quote within the given category
    return "New Quote Page"

@app.route('/categories/<category_name>/<int:quote_id>/edit')
def EditQuotePage():
    # Edit a quote if you are the user that creates/manages that quote
    return "Edit Quote Page"

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)