from flask import Flask, redirect, render_template, request, flash, redirect, session, g
import flask
import json
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests, random
from datetime import datetime
import threading
from flask_cors import CORS

from models import db, connect_db, User, UserPreference, FavoritePet, MaybePet, FavoriteOrg, Comment
from forms import UserForm, LoginForm, UserPreferenceForm, CommentForm
from config_info import API_KEY,API_SECRET, SECRET_KEY

# create the app
app = Flask(__name__)
CORS(app)

# configure the postgresql database, relative to the app instance folder
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///furmily_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

connect_db(app)

# db.create_all()


# ============ API call requirements ======================#
# from stackoverflow https://stackoverflow.com/questions/2697039/python-equivalent-of-setinterval

# ACCESS_TIME = '0'
# ACCESS_TOKEN =''

# def setInterval(func,time):
#     e = threading.Event()
#     while not e.wait(time):
#         func()

def get_token():
    res = requests.post('https://api.petfinder.com/v2/oauth2/token', data={'grant_type':'client_credentials', 'client_id': API_KEY, 'client_secret': API_SECRET})
    # ACCESS_TIME = datetime.now()
    data=res.json()
    # ACCESS_TOKEN = data['access_token']
    return data['access_token']

ACCESS_TOKEN = get_token()
print(f'1:{ACCESS_TOKEN}')

# setInterval(get_token,3600)
# option1 - maybe I can get datestamp when I get access token. Then if(ACCESS_TOKEN), check datetime to see if it's past 3600 seconds. if so, we need to get new token.

# option2 - petfinder API wrapper for login support :https://github.com/aschleg/petpy

API_BASE_URL = 'https://api.petfinder.com/v2'
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# ==========================================================#

CURR_USER_KEY = 'curr_user'

org_list = []
# ============================================================#
#=== signup/login/logout g.user & Session assign handling ====#
# ============================================================#
# this will run before every request."before_request" =Register a function to run before each request.
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
        # g is an object for storing data during the application context of a running Flask web app. By adding the user to g, we can use user info anywhere.

    else:
        g.user = None


def do_login(user):
    """Log in user."""
    # user is put in session
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

# ============ Sing Up User  ======================#
@app.route('/signup', methods=["GET", "POST"])
def signup():
    """
    Handle user signup.Create new user and add to DB. Redirect to home page.If form not valid, present form. If the there already is a user with that username: flash message
    and re-present form.
    """
    # make sure no one is logged in before signup
    do_logout()

    form = UserForm()

    if form.validate_on_submit():
        try:
            user =User.signup(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            db.session.commit()
        
        except IntegrityError:
            flash("Username already taken", 'danger')

        do_login(user)

        return redirect('/questions')

    else:
        return render_template('signup.html', form=form)

# ============ LOG IN User  ======================#
@app.route("/login", methods=["GET", "POST"])
def login():
    """user login page"""
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            username=form.username.data,
            password=form.password.data
        )

        if user:
            do_login(user)
            return redirect("/questions")
        else:
            flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():

    do_logout()

    flash('You have logged out successfully', 'success')
    return redirect('/home')

@app.route('/users/profile/<int:user_id>', methods=['GET', 'POST'])
def show_edit_user(user_id):
    
    # if g.user.id is not equial to user id:
    #     flash('Please log in')
    #     return redirect('/login')
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.updateUser(form.username.data, form.email.data, form.password.data)

        db.session.commit()

        flash('Your Info was Successfully Updated!', 'success')

        return render_template('user_profile.html', form = form, user=user)
    
    return render_template('user_profile.html', form = form, user=user)

# ============================================================#
#========= End of User Signup & Login & Logout ===============#
# ============================================================#


@app.route("/")
def root():
    """Homepage"""
    return redirect('/home')

@app.route('/home')
def home():
    #===== show adoptable pet available, but need to think of way to count all available animals since API show only up to 100. 
    # res = requests.get(f'{API_BASE_URL}/animals', headers=headers, params={'status': 'adoptable'})
    # data=res.json()
    # num =len(data['animals'])
    if g.user:
        return redirect('/questions')
    
    return render_template('home.html')

# ================ Show all Fav and maybe pet =================================
@app.route('/pets/users/<int:user_id>')
def user_page(user_id):
    """show user profile including preference, favorite pets, maybe pets saved"""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/home")
    # do I need to put if g.user_id does not equal  to user_id?


    form=CommentForm()

    user = User.query.get_or_404(user_id)
    fav_pets_id = [pet.pet_id for pet in FavoritePet.query.all()]
    fav_pets =[]
    for pet_id in fav_pets_id:
         response = requests.get(f'{API_BASE_URL}/animals/{pet_id}', headers=headers)
         data = response.json()
        #  print(data)
         fav_pets.append(data['animal'])

    comments = Comment.query.filter_by(user_id = g.user.id)

       
    maybe_pets_id = [pet.pet_id for pet in MaybePet.query.all()]
    maybe_pets =[]
    for pet_id in maybe_pets_id:
         response = requests.get(f'{API_BASE_URL}/animals/{pet_id}', headers=headers)
         data = response.json()
         maybe_pets.append(data['animal'])
    # make api calls to get data for each pets and store that in dictionary
    # each rendered animal will have comments section, delete button    

    return render_template('users_pets.html', user=user, fav_pets=fav_pets, maybe_pets=maybe_pets, comments = comments, form=form)


#============= Get user's preference and show result ======================= 
@app.route('/questions', methods=["GET", "POST"])
def show_questions():

    form = UserPreferenceForm()

    # res = requests.get(f'{API_BASE_URL}/types', headers=headers)
    # data = res.json()
    # pet_types =[(item['name'], item['name']) for item in data['types']]
    # form.pet_type.choices = pet_types

    if form.validate_on_submit():
        # if user not logged in, how do I do this?
        
        user_pref = UserPreference(# raise
        user_id = g.user.id,
        pet_type = form.pet_type.data,
        size = form.size.data,
        gender = form.gender.data,
        age = form.age.data,
        # good_with_children = 'true' if form.good_with_children.data == True else 'false',
        # house_trained = 'true' if form.house_trained.data == True else 'false',
        # special_need = 'true' if form.special_need.data == True else 'false',
        zipcode = form.zipcode.data)

        
        db.session.add(user_pref)
        db.session.commit()

        response = requests.get(f'{API_BASE_URL}/animals', headers=headers, params={'type': user_pref.pet_type, 'size': user_pref.size, 'gender': user_pref.gender, 'age': user_pref.age, 'location': user_pref.zipcode, 'limit': 50, 'status': 'adoptable'})
        match_data = response.json()
        list_of_animals = match_data['animals']

        for animal in list_of_animals:
            if len(animal['photos']) ==0:
                list_of_animals.remove(animal)
        
        # match_data =user_pref.show_matches
        if len(list_of_animals) == 0 :
            flash('No Match Found. Please Try Again.', 'danger')
            return redirect('/questions')
        elif len(list_of_animals) > 10:
            list_of_animals= random.sample(list_of_animals, 10) # randomly choose 10 from the list and make new list
            return render_template('match_result.html', list_of_animals=list_of_animals)            
        
        return render_template('match_result.html', list_of_animals=list_of_animals)

    return render_template('questions.html', form=form)

# =============adding pets to Favorite or Maybe========================
@app.route('/likes', methods=['POST'])
def add_fav():
    received_data=request.get_json()
    print(f"received_data{received_data}")
    return_data = {
        'status':'success',
        'message': f'received:{received_data["animal"]}'

    }

    # =====this logic is not working why???========
    all_fav=FavoritePet.query.all()# get users fav pet, if aleady exist, don't add no action
    if FavoritePet.query.filter_by(pet_id=received_data['animal']) in all_fav:
        return_data = {
        'status':'already in database',
        'message': f'received:{received_data["animal"]}'
        }
        
        return flask.Response(response=json.dumps(return_data), status=201)
         
    else:
        # response = requests.get(f'{API_BASE_URL}/animals', headers=headers, params={'type': user_pref.pet_type, 'size': user_pref.size, 'gender': user_pref.gender, 'age': user_pref.age, 'location': user_pref.zipcode, 'limit': 50, 'status': 'adoptable'})
        # match_data = response.json()
        # list_of_animals = match_data['animals']

        # ここでAPIコールしてanimalIDから得た情報でFavaritePetをDatabaseに追加する
        # 追加する情報は？
        # pet_id
        # imgurl
        # pet_name
        # pet_description
        # location_city
        # location_state
        # organization_id

        # get organization info 
        
        favPet = FavoritePet(
        pet_id = received_data['animal'],
        user_id = g.user.id)

        db.session.add(favPet)
        db.session.commit()

        return flask.Response(response=json.dumps(return_data), status=201)

@app.route('/maybe', methods=['POST'])
def add_maybe():
    received_data=request.get_json()
    print(f"received_data{received_data}")
    return_data = {
        'status':'success',
        'message': f'received:{received_data["animal"]}'
    }

    all_maybe=MaybePet.query.all()
    if MaybePet.query.filter_by(pet_id=received_data['animal']) in all_maybe:
        return_data = {
        'status':'already in database',
        'message': f'received:{received_data["animal"]}'
        }

        return flask.Response(response=json.dumps(return_data), status=201)

    maybePet = MaybePet(
    pet_id = received_data['animal'],
    user_id = g.user.id)

    db.session.add(maybePet)
    db.session.commit()

    return flask.Response(response=json.dumps(return_data), status=201)


# ============= DELETE user's favorite & maybe pet===========================
@app.route('/delete-fav', methods=['POST'])
def delete_fav():
    received_data=request.get_json()
    print(f"received_data{received_data}")
    return_data = {
        'status':'successfully deleted',
        'message': f'received:{received_data["animal"]}'
    }

    FavoritePet.query.filter_by(pet_id=received_data['animal']).delete()
    db.session.commit()

    return flask.Response(response=json.dumps(return_data), status=201)

@app.route('/delete-maybe', methods=['POST'])
def delete_maybe():
    received_data=request.get_json()
    print(f"received_data{received_data}")
    return_data = {
        'status':'successfully deleted',
        'message': f'received:{received_data["animal"]}'
    }

    MaybePet.query.filter_by(pet_id=received_data['animal']).delete()
    db.session.commit()

    return flask.Response(response=json.dumps(return_data), status=201)

# ================add user comments of a pet to DB ===========================
@app.route('/comments/<int:pet_id>', methods=['POST'])
def add_pet_comments(pet_id):
    received_data=request.get_json()
    print(f"received_data{received_data}")
    return_data = {
        'status':'successful',
        'message': f'received:pet_id {received_data["animal"]}, comment:{received_data["comment"]}'
    }

    comment = Comment(
        user_id=g.user.id,
        pet_id =pet_id,
        comment=received_data['comment']
    )

    db.session.add(comment)
    db.session.commit()

    return flask.Response(response=json.dumps(return_data), status=201)

# ==============org search ==============================
@app.route('/org-search', methods=['GET'])
def show_search_page():
    
    return render_template('org_search.html')

@app.route('/org-results', methods=['POST'])
def search_result():

    # org_list = []

    user_query = request.args.get('search-word')
    response = requests.get(f'{API_BASE_URL}/organizations', headers=headers, params={'query': user_query})
    data = response.json()
    orgs = data['organizations']
    print(orgs)

    return render_template('org_results.html', user_query=user_query, orgs_list=orgs)
    
    