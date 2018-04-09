from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catlog, CatlogItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catlog"


# Connect to Database and create database session
engine = create_engine('sqlite:///catlog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """
    Generate a ramdom token will be used to provent anti-forgery STATE
    attack and render the login template
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API and places it inside
    a session variable that will be used to better serve the user.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!!!!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    """Helper method for gconnect, create a new user to database"""
    newUser = User(name=login_session['username'],
                   email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Helper method for gconnect, get user info from database"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Helper method for gconnect, get user info from database"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    """
    Disconnect user from google plus sign in and clean the login session
    """
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        login_session.clear()
        flash('Successfully logged out')
        return redirect(url_for('showCatlogs'))
    else:
        response = make_response(json.dumps('Failed to revoke' +
                                 'token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/catlog')
def showCatlogs():
    """Render the catlog page using the catlogs.html template"""
    catlogs = session.query(Catlog).order_by(asc(Catlog.name))
    return render_template('catlogs.html',
                           catlogs=catlogs,
                           login_session=login_session)


@app.route('/catlog/<int:catlog_id>/')
@app.route('/catlog/<int:catlog_id>/item/')
def showItem(catlog_id):
    """Render the item page using the item.html template"""
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    items = session.query(CatlogItem).filter_by(catlog_id=catlog_id).all()
    return render_template('item.html', items=items, catlog=catlog)


@app.route('/catlog/<int:catlog_id>/<int:item_id>/')
def showItemInfo(catlog_id, item_id):
    """Render the item info page using the itemDescription.html template"""
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    item = session.query(CatlogItem).filter_by(id=item_id).one()
    return render_template('itemDescription.html', item=item, catlog=catlog)


@app.route('/catlog/<int:catlog_id>/item/new/', methods=['GET', 'POST'])
def newItem(catlog_id):
    """
    function receive form data from user and create a new item to
    store this item in the database.
    """
    if 'username' not in login_session:
        flash('user must be login to modify the item')
        return redirect(url_for('showCatlogs'))
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    if request.method == 'POST':
        newItem = CatlogItem(name=request.form['name'],
                             description=request.form['description'],
                             catlog_id=catlog_id,
                             user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItem', catlog_id=catlog_id))
    else:
        return render_template('newItem.html', catlog=catlog)


@app.route('/catlog/<int:catlog_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(catlog_id, item_id):
    """
    function receive form data from user and edit the item and update the
    item in the database
    """
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    editItem = session.query(CatlogItem).filter_by(id=item_id).one()
    if 'username' not in login_session:
        flash('user must be login to modify the item')
        return redirect(url_for('showCatlogs'))
    if editItem.user_id != login_session['user_id']:
        print "editItem.user_id: " + str(editItem.user_id)
        print "login_session['user_id']: " + str(login_session['user_id'])
        flash('You are not authorized to edit this restaurant' +
              'Please create your own restaurant in order to edit')
        return redirect(url_for('showItem', catlog_id=catlog_id))

    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        return redirect(url_for('showItemInfo',
                                catlog_id=catlog_id,
                                item_id=item_id))
    else:
        return render_template('editItem.html',
                               catlog=catlog,
                               editItem=editItem)


@app.route('/catlog/<int:catlog_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(catlog_id, item_id):
    """
    function receive form data from user and delete the item and delete the
    item in the database
    """
    if 'username' not in login_session:
        flash('user must be login to modify the item')
        return redirect(url_for('showCatlogs'))
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    try:
        itemToDelete = session.query(CatlogItem).filter_by(id=item_id).one()
    except:
        return redirect(url_for('showItem', catlog_id=catlog_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showItem', catlog_id=catlog_id))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete, catlog=catlog)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
