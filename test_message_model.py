import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test the model for messages"""

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.userid = 9001
        user = User.signup('tester','test@test.com','test',None)
        user.id=self.userid
        db.session.commit()
        self.user = User.query.get(self.userid)
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Test that the model works"""
        message = Message(text='test',user_id=self.userid)
        db.session.add(message)
        db.session.commit()
        self.assertEqual(len(self.user.messages),1)
        self.assertEqual(self.user.messages[0].text, 'test')

    def test_message_likes(self):
        """Test liking functionality with the models"""
        user2 = User.signup('test2','test2@test.com','test2',None)
        message = Message(text='test2',user_id=self.userid)
        userid2 = 9002
        user2.id = userid2
        db.session.add_all([user2,message])
        user2.likes.append(message)
        db.session.commit()
        likes = Likes.query.filter(Likes.user_id==userid2).all()
        self.assertEqual(len(likes),1)
        self.assertEqual(likes[0].message_id,message.id)
