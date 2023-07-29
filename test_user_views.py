import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, connect_db, Likes
from bs4 import BeautifulSoup

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

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users"""

    def setUp(self):
        """Create test client and add sample data"""
        
        db.drop_all()
        db.create_all()
        self.client=app.test_client()
        
        self.user0 = User.signup('test0','user0@email.com','user0',None)
        self.user0id = 9000
        self.user0.id = self.user0id
        self.user1 = User.signup('test1','user1@email.com','user1',None)
        self.user1id = 9001
        self.user1.id = self.user1id
        self.user2 = User.signup('user2','user2@email.com','user2',None)
        self.user2id = 9002
        self.user2.id = self.user2id
        self.user3 = User.signup('user3','user3@email.com','user3',None)
        self.user3id = 9003
        self.user3.id = self.user3id
        db.session.commit()

        self.m1 = Message(id=5001, text='test number one', user_id=self.user0id)
        self.m2 = Message(id=5002, text='test number two', user_id=self.user0id)
        self.m3 = Message(id=5003, text='test number three', user_id=self.user1id)
        db.session.add_all([self.m1,self.m2,self.m3])
        db.session.commit()

        self.l1 = Likes(user_id=self.user0id, message_id=5003)
        db.session.add(self.l1)
        db.session.commit()

        #User0 is following User1 and User2. User1 is following User0
        self.f1 = Follows(user_being_followed_id=self.user1id, user_following_id=self.user0id)
        self.f2 = Follows(user_being_followed_id=self.user2id, user_following_id=self.user0id)
        self.f3 = Follows(user_being_followed_id=self.user0id, user_following_id=self.user1id)
        db.session.add_all([self.f1,self.f2,self.f3])
        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_index(self):
        with self.client as client:
            resp = client.get('/users')

            self.assertIn('@test0',str(resp.data))
            self.assertIn('@test1',str(resp.data))
            self.assertIn('@user2',str(resp.data))
            self.assertIn('@user3',str(resp.data))

    def test_users_search(self):
        with self.client as client:
            resp = client.get('/users?q=test')

            self.assertIn('@test0',str(resp.data))
            self.assertIn('@test1',str(resp.data))
            self.assertNotIn('@user2',str(resp.data))
            self.assertNotIn('@user3',str(resp.data))

    def test_user_page(self):
        with self.client as client:
            resp = client.get(f'/users/{self.user0id}')
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@test0',str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            li = soup.find_all('li',{'class':'stat'})
            self.assertEqual(len(li),4)
            #Test for 2 messages
            self.assertIn('2',li[0].text)
            #Test for 2 following
            self.assertIn('2',li[1].text)
            #Test for 1 follower
            self.assertIn('1',li[2].text)
            #Test for 1 like
            self.assertIn('1',li[3].text)


    def test_add_like(self):
        m = Message(id=5004, text='test message four',user_id = self.user1id)
        db.session.add(m)
        db.session.commit()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user0id
            resp = client.post('/users/add_like/5004',follow_redirects=True)
            self.assertEqual(resp.status_code,200)
            likes=Likes.query.filter(Likes.message_id==5004).all()
            self.assertEqual(len(likes),1)
            self.assertEqual(likes[0].user_id, self.user0id)

    def test_unlike(self):
        message = Message.query.get(5003)
        self.assertIsNotNone(message)
        self.assertNotEqual(message.user_id, self.user0id)
        like = Likes.query.filter(Likes.user_id==self.user0id and Likes.message_id==message.id).one()
        self.assertIsNotNone(like)
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user0id
            resp = client.post(f'/users/del_like/{message.id}', follow_redirects=True)
            self.assertEqual(resp.status_code,200)
            likes=Likes.query.filter(Likes.message_id==message.id).all()
            self.assertEqual(len(likes),0)

    def test_unauth_like(self):
        message = Message.query.get(5003)
        self.assertIsNotNone(message)
        likes_num = Likes.query.count()
        with self.client as client:
            resp = client.post('/users/add_like/5003',follow_redirects=True)
            self.assertEqual(resp.status_code,200)
            self.assertIn('Access unauthorized', str(resp.data))
            self.assertEqual(likes_num,Likes.query.count())

    def test_show_following(self):
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user0id
            resp = client.get(f'/users/{self.user0id}/following')
            self.assertEqual(resp.status_code,200)
            self.assertIn('@test1',str(resp.data))
            self.assertIn('@user2',str(resp.data))
            self.assertNotIn('@user3',str(resp.data))
            
    def test_unauth_following_access(self):
        with self.client as client:
            resp = client.get(f'/users/{self.user0id}/following',follow_redirects=True)
            self.assertEqual(resp.status_code,200)
            self.assertIn('Access unauthorized',str(resp.data))

    def test_unauth_followers_access(self):
        with self.client as client:
            resp = client.get(f'/users/{self.user0id}/followers',follow_redirects=True)
            self.assertEqual(resp.status_code,200)
            self.assertIn('Access unauthorized',str(resp.data))