"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup('test1','test1@email.com','password1',None)
        userid1 = 1000
        user1.id = userid1
        user2 = User.signup('test2','test2@email.com','password2',None)
        userid2 = 2000
        user2.id = userid2

        db.session.commit()

        self.user1 = User.query.get(userid1)
        self.userid1 = userid1
        self.user2 = User.query.get(userid2)
        self.userid2 = userid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

#Following Tests#####################################################################
    def test_user_follows(self):
        """Test following functionality"""
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.following),0)
        self.assertEqual(len(self.user2.followers),1)
        self.assertEqual(len(self.user1.following),1)
        self.assertEqual(len(self.user1.followers),0)

        self.assertEqual(self.user1.following[0].id, self.userid2)
        self.assertEqual(self.user2.followers[0].id, self.userid1)

    def test_is_following(self):
        """Test the is_following method"""
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        """Test the is_followed_by method"""
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

#Signup Tests##########################################################################

    def test_valid_signup(self):
        test = User.signup('tester','tester@test.com','test123',None)
        testid = 3000
        test.id = 3000
        db.session.commit()

        test = User.query.get(testid)
        self.assertIsNotNone(test)
        self.assertEqual(test.username,'tester')
        self.assertEqual(test.email, 'tester@test.com')
        self.assertNotEqual(test.password,'test123')

    def test_invalid_username_signup(self):
        test = User.signup(None,'tester@test.com','123',None)
        testid = 123
        test.id=testid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup('tester','tester@test.com','',None)
        with self.assertRaises(ValueError) as context:
            User.signup('tester','tester@test.com',None,None)

#Authentication Tests#####################################################################
    def test_authentication(self):
        user = User.authenticate(self.user1.username,'password1')
        self.assertIsNotNone(user)
        self.assertEqual(user.id,self.userid1)

    def test_invalid_username_auth(self):
        self.assertFalse(User.authenticate('aslk','password1'))

    def test_invalid_password_auth(self):
        self.assertFalse(User.authenticate('test1','asldjkhgf'))