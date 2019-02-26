from flask import Flask, render_template, request, redirect, \
    jsonify, flash, session as login_session, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, lazyload
from database_setup import Base, Category, Item
import random
import string
import json
from datetime import datetime, timedelta
import httplib2
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


engine = create_engine('sqlite:///catalogapp.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

try:
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    # Create some data
    has_data = session.query(Category).all()
    if not has_data:
        print("Creating some data...")

        item1 = Item(name='Cool Shirt',
                     description='Just a cool shirt.',
                     owner_mail='reismatheus97@gmail.com')
        item2 = Item(name='Really Cool Shirt',
                     description='A realy cool shirt.',
                     owner_mail='reismatheus97@gmail.com')

        c1 = Category(name='Clothes', items=[item1, item2])
        session.add(c1)

        item3 = Item(name='Star Wars Battlefront II',
                     description='An epic game from the Star Wars saga.',
                     owner_mail='reismatheus97@gmail.com')
        item4 = Item(name='FIFA 19',
                     description='Play with the bests!',
                     owner_mail='reismatheus97@gmail.com')
        c2 = Category(name='Games',
                      date_created=datetime.now()+timedelta(seconds=60),
                      items=[item3, item4])
        session.add(c2)

        item5 = Item(name='Star Wars III',
                     description='The best movie on the Star Wars saga.',
                     owner_mail='reismatheus97@gmail.com')
        c3 = Category(name='Movies',
                      date_created=datetime.now()-timedelta(seconds=60),
                      items=[item5])
        session.add(c3)

        session.commit()
        print("... some data are here!")

except Exception as excp:
    print("Unable to connect to database: %s" % excp)


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
        oauth_flow = flow_from_clientsecrets(
            'client_secret.json',
            scope=['https://www.googleapis.com/auth/userinfo.profile']
        )
        oauth_flow.redirect_uri = 'http://localhost:5000'
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

    stored_access_token = \
        login_session.get('access_token')
    stored_gplus_id = \
        login_session.get('gplus_id')

    if stored_access_token is not None and \
            gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'
        ), 200)
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

    if 'name' in data:
        username = data['name']
    else:
        username = 'UNNAMED_USER'

    login_session['username'] = username
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = '<div class="welcome-div">'
    output += '<h3>Welcome, '
    output += login_session['username']
    output += '!</h3>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 150px; height: 150px;' \
              'border-radius: 150px;-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '
    output += '</div>'
    flash("You are now logged in as %s" % login_session['username'])

    return output


@app.route('/login')
def login_page():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits
    ) for x in range(32))

    login_session['state'] = state
    return render_template('login.html',
                           active_route='login',
                           login_session=login_session)


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps(
                'Successfully disconnected.'
            ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400)
        )

        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog_app/JSON')
def catalog_app_json():
    all_categories = session.query(Category)\
                        .options(lazyload(Category.items)).all()
    return jsonify(
        Catalog=[i.serialize_with_relations for i in all_categories]
    )


@app.route('/logout')
def logout():
    return render_template('logout.html', active_route='')


@app.route('/something_bad')
def something_bad():
    return render_template('something_bad.html',
                           active_route='',
                           error="Something bad happened.",
                           login_session=login_session)


@app.route('/not_allowed')
def not_allowed():
    return render_template('something_bad.html',
                           active_route='',
                           error="Sorry, you're not allowed to do that.",
                           login_session=login_session)


@app.route('/')
def home_page():
    try:
        categories = session.query(Category).order_by().all()
        items = session.query(Item).all()
        return render_template('content.html',
                               categories=categories,
                               items=items,
                               active_route='home',
                               login_session=login_session)
    except Exception as e:
        flash('An error occurred...')
        print("Exception: %s" % e)
        return redirect('/something_bad')


@app.route('/category/<int:category_id>')
def show_category(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        items = session.query(Item).filter_by(category_id=category_id).all()
        return render_template('show_category.html',
                               category=category,
                               items=items,
                               active_route='',
                               login_session=login_session)
    except Exception as e:
        print("Exception: %s" % e)
        flash('An error occurred...')
    return redirect('/something_bad')


@app.route('/category/new', methods=['POST'])
def create_category():
    if 'username' not in login_session:
        return redirect('/not_allowed')
    try:
        new_category = Category(name=request.form['name'])
        session.add(new_category)
        session.commit()
        msg = "Category %s successfully created!" % new_category.name

    except Exception as e:
        print("Exception: %s" % e)
        msg = "An error occurred..."

    return jsonify(msg)


@app.route('/category/<int:category_id>/item/new', methods=['POST', 'GET'])
def create_item(category_id):
    if 'username' not in login_session:
        return redirect('/not_allowed')

    try:
        category = session.query(Category).filter_by(id=category_id).one()
        if category is not None:
            if request.method == 'POST':
                if request.form['name']:
                    item = Item(name=request.form['name'],
                                description=request.form['description'],
                                category_id=category_id,
                                owner_mail=login_session['email'])
                    session.add(item)
                    session.commit()
                    msg = 'Item successfully created'
                    location = '/category/%s' % category.id
                else:
                    msg = 'Invalid form values!'
                    location = '/category/%s/item/new' % category.id

            else:
                return render_template('create_item.html',
                                       category=category)
        else:
            flash('Invalid category!')
            return redirect('/something_bad')

    except Exception as e:
        print("Exception: %s" % e)
        msg = 'An error occurred...'
        location = '/something_bad'

    flash(msg)
    return redirect(location)


@app.route('/category/<int:category_id>/item/<int:item_id>/edit',
           methods=['POST'])
def update_item(category_id=0, item_id=0):
    """
    This method lets an user logged-in
    but not the owner of item to submit
    the form and get a "not allowed"
    response to illustrate the bounds
    built by the authorization module.
    """

    if 'username' not in login_session:
        return redirect('/not_allowed')

    try:
        item = session.query(Item) \
            .filter_by(category_id=category_id) \
            .filter_by(id=item_id).one()

        if login_session['email'] == item.owner_mail:
            if request.form['name']:
                item.name = request.form['name']
                item.description = request.form['description']
                session.add(item)
                session.commit()
                msg = 'Item successfully edited!'
                location = '/category/%s' % item.category_id
            else:
                msg = 'Invalid form values!'
                location = '/category/%s/item/new' % item.category_id
        else:
            msg = 'Only an owner of a item can edit it!'
            location = '/not_allowed'

    except Exception as e:
        print("Exception: %s" % e)
        msg = 'An error occurred...'
        location = '/something_bad'

    flash(msg)
    return redirect(location)


@app.route('/category/<int:category_id>/item/<int:item_id>')
def show_item(item_id, category_id):
    try:
        item = session.query(Item) \
            .filter_by(category_id=category_id) \
            .filter_by(id=item_id) \
            .one()

        return render_template('show_item.html',
                               item=item,
                               active_route='home',
                               login_session=login_session)
    except Exception as e:
        print("Exception: %s" % e)
        flash('An error occurred...')
        return redirect('/something_bad')


@app.route('/category/<int:category_id>/item/<int:item_id>/delete',
           methods=['POST'])
def delete_item(category_id, item_id):
    """
    This method lets an user logged-in
    but not the owner of item to submit
    the form and get a "not allowed"
    response to illustrate the bounds
    built by the authorization module.
    """
    try:
        if login_session['email']:
            item = session.query(Item) \
                .filter_by(category_id=category_id) \
                .filter_by(id=item_id).one()

            if login_session['email'] == item.owner_mail:
                session.delete(item)
                session.commit()
                msg = 'Item successfully deleted!'
                location = '/category/%s' % item.category_id
            else:
                msg = 'Only an owner of a item can delete it!'
                location = '/not_allowed'

        else:
            msg = 'Only logged in users can delete items!'
            location = '/not_allowed'
    except Exception as e:
        print("Exception: %s" % e)
        msg = 'An error occurred...'
        location = '/something_bad'

    flash(msg)
    return redirect(location)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
