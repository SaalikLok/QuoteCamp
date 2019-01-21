# QuoteCamp 🏕
### A crowdsourced catalog of quotes

## Motivation

QuoteCamp is a project created to organize and collect quotes.
Users create accounts in order to add a quote to a category.

## Running Locally

1. Make sure Vagrant and Virtualbox is installed on your machine. Open a terminal.
2. Use `vagrant up` to the start the VM
3. Navigate to the 'catalog' folder with `cd vagrant/catalog`
4. On the first use of the project, set up the database by running the command: `python db_setup.py`
5. Prepopulate the database with the quote categories by running the command: `python populatedb.py`
6. Launch the server with the command: `python application.py`
7. Visit 'http://localhost:5000/' to run the application.

## API

JSON endpoints are available for developers to use to pull QuoteCamp quotes into their own applications.

- For a random quote: /categories/randomquote/JSON
- For all quotes: /JSON
- For quotes within a category: /categories/(category)/JSON