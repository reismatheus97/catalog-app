from flask import Flask, render_template, request, redirect, \
    jsonify, url_for, flash, session as login_session, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
import random
import string
import json
import httplib2
import requests


from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


engine = create_engine('postgresql://catalogadmin:root@localhost:5432/catalog')
Base.metadata.bind = engine

try:
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
except ConnectionError as e:
    print("Unable to connect to database: %s" % e)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
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
        print("Token's client ID does not match app's.")
        print(result['issued_to'])
        print(CLIENT_ID)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
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
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/logout')
def logout():
    return render_template('logout.html', active_route='')


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
def home_page():
    categories = session.query(Category).order_by().all()
    items = session.query(Item).all()
    return render_template('content.html',
                           categories=categories,
                           items=items,
                           active_route='home')


@app.route('/login')
def login_page():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', active_route='login', login_session=login_session)


@app.route('/category/<int:category_id>')
def show_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('show_category.html', category=category, active_route='home')


@app.route('/category/new', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        new_category = Category(name=request.form['name'])
        session.add(new_category)
        msg = "Category %s successfully created!" % new_category.name
        print(msg)
        session.commit()
        return jsonify(msg=msg)
    else:
        render_template('new_category.html', active_route='home')


@app.route('/category/json')
def get_categories_json():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/category/<int:category_id>/json')
def get_category_json(category_id):
    category_edit = session.query(Category).filter_by(id=category_id).one()
    return jsonify(category=category_edit.serialize)


@app.route('/category/<int:category_id>/item/new', methods=['POST'])
def create_item(category_id):
    item = Item(name=request.form['name'],
                description=request.form['description'],
                category_id=category_id)
    session.add(item)
    session.commit()
    msg = 'Item successfully created'
    return jsonify(item=item.serialize, msg=msg)


@app.route('/item/<int:item_id>/edit', methods=['POST'])
@app.route('/category/<int:category_id>/item/<int:item_id>/edit', methods=['POST'])
def update_item(category_id=0, item_id=0):
    if category_id:
        item = session.query(Item) \
            .filter_by(category_id=category_id) \
            .filter_by(id=item_id).one()
    else:
        item = session.query(Item) \
            .filter_by(id=item_id).one()

    if request.form['name'] and request.form['description']:
        print('Item name %s' % item.name)
        print('Item description %s' % item.description)
        item.name = request.form['name']
        item.description = request.form['description']

    session.add(item)
    session.commit()
    flash('Item successfully edited!');
    return redirect('/')


@app.route('/item/<int:item_id>')
def show_item(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('show_item.html', item=item, active_route='home', login_session=login_session)


@app.route('/item/<int:item_id>/delete', methods=['POST'])
@app.route('/category/<int:category_id>/item/<int:item_id>/delete', methods=['POST'])
def delete_item(category_id=0, item_id=0):

    if login_session['username']:
        if category_id:
            item = session.query(Item) \
                .filter_by(category_id=category_id) \
                .filter_by(id=item_id).one()
        else:
            item = session.query(Item) \
                .filter_by(id=item_id).one()

        # If user is the item creator: delete
        # Else: not allowed

        session.delete(item)
        session.commit()
        flash('Item successfully deleted!');

    return redirect('/')


@app.route('/category/<int:category_id>/item/json')
def get_category_items_json(category_id):
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/json')
def get_category_item_json(category_id, item_id):
    item = session.query(Item)\
            .filter_by(category_id=category_id)\
            .filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)