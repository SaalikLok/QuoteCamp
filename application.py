from flask import Flask
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, User, Quote

engine = create_engine('sqlite:///quotecamp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/hello')
def HelloWorld():
    return "Hello Home Page"

@app.route('/login')
def LoginPage():
    # Show the login auth page
    return "Login Page"

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
    app.debug = True
    app.run(host='0.0.0.0', port=5000)