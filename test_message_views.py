"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.userid=1001
        self.testuser.id=self.userid
        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_unauth(self):
        """Test that access is denied for an unauthorized user"""
        with self.client as client:
                with client.session_transaction() as session:
                    session[CURR_USER_KEY] = 9999
                resp = client.post('/messages/new', data={'text':'test'},follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn('Access unauthorized',str(resp.data))

    def test_message_show(self):
        message = Message(id=2001,text='test',user_id=self.userid)
        db.session.add(message)
        db.session.commit()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.userid
            m = Message.query.get(2001)
            resp = client.get(f'/messages/{m.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text,str(resp.data))

    def test_invalid_message_show(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.userid
        resp = client.get('/messages/99999')
        self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        message = Message(id=2002,text='test',user_id=self.userid)
        db.session.add(message)
        db.session.commit()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.userid
            resp = client.post('/messages/2002/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            message = Message.query.get(2002)
            self.assertIsNone(message)

    def test_unauth_message_delete(self):
        user2 = User.signup(username='test2',email='test2@test.com',password='test2',image_url=None)
        user2.id=1002
        message = Message(id=2003,text='test',user_id=self.userid)
        db.session.add_all([user2,message])
        db.session.commit()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 1002
            resp = client.post('/messages/2003/delete',follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized',str(resp.data))
            message = Message.query.get(2003)
            self.assertIsNotNone(message)

    def test_no_auth_message_delete(self):
        message = Message(id=2004,text='test',user_id=self.userid)
        db.session.add(message)
        db.session.commit()
        with self.client as client:
            resp = client.post('/messages/2004/delete',follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized',str(resp.data))
            message = Message.query.get(2004)
            self.assertIsNotNone(message)
