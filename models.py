"""Models for Furmily app."""

from datetime import datetime
# import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
# import bycript
from flask_bcrypt import Bcrypt

# create bycrypt instance
bcrypt = Bcrypt()

# create the extension
db = SQLAlchemy()

# ========================== function to run database ================================#
# this function is imported and used in app.py file
def connect_db(app):
    """Connect to database."""

    db.app = app
    # initialize the app with the extension
    db.init_app(app)

# =================================== USER class ====================================#

class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    username = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    def __repr__(self):
        return f'<User #{self.id}: {self.username}>'

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

# =================================== USER Preference class ====================================#

class UserPreference(db.Model):

    __tablename__ = 'user_preference'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id =db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable = False,
        primary_key=True
    )

    pet_type = db.Column(
        db.Text,
        nullable=False
    )

    # breed = db.Column(
    #     db.Text
    # )

    size = db.Column(
        db.Text
    )

    gender = db.Column(
        db.Text
    )

    age = db.Column(
        db.Text
    )

    # good_with_children = db.Column(
    #     db.Text
    # )

    # house_trained = db.Column(
    #     db.Text
    # )

    # special_need = db.Column(
    #     db.Text
    # )

    zipcode = db.Column(
        db.Integer
    )

    # def show_matches(user_id, pet_type, size, gender, age, good_with_children, house_trained, special_need, zipcode):
    #     response = requests.get(f'{API_BASE_URL}/animals', headers=headers, params={'type': pet_type, 'size': size, 'gender': gender, 'age': age, 'good_with_children': good_with_children, 'house_trained':house_trained, 'special_needs':special_need, 'location': zipcode, 'limit': 100, 'status': 'adoptable'})
    #     match_data = response.json()
    #     return match_data


# =================================== Favorite Pet class ====================================#

class FavoritePet(db.Model):

    __tablename__ ='favorite_pets'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id =db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable = False,
        primary_key=True
    ) 

    pet_id = db.Column(
        db.Integer,
        nullable=False
    )

    # datetime = db.Column(
        
    # )

# =================================== Maybe Pet class ====================================#        
class MaybePet(db.Model):

    __tablename__ ='maybe_pets'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id =db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable=False,
        primary_key=True
    )    

    pet_id = db.Column(
        db.Integer,
        nullable=False
    )

# =================================== Favorite Organization class ====================================#
class FavoriteOrg(db.Model):

    __tablename__ ='favorite_orgs'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id =db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable = False
    )

    org_id = db.Column(
        db.Text,
        nullable=False
    )

# =================================== Comments class ====================================#

class Comment(db.Model):

    __tablename__ ='comments'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id =db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable= False
    )    

    org_id = db.Column(
        db.Text
    )

    pet_id = db.Column(
        db.Integer
    )

    comment= db.Column(
        db.Text
    )

