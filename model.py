
from google.appengine.ext import db

class Server(db.Model):
    """Models a game server that can host a match"""
    host = db.StringProperty()
    free = db.BooleanProperty()
    
    @classmethod
    def get_free(cls):
        return cls.all().filter("free =", True).get()

class Player(db.Model):
    """Models an individual Player, with username, email, and password"""
    username = db.StringProperty()
    password = db.StringProperty()
    
    joined = db.DateTimeProperty(auto_now_add=True)
    
    # TODO: take this out of here?
    searching = db.BooleanProperty()
    match_server = db.ReferenceProperty(Server, collection_name='players')


class MatchHistory(db.Model):
    """Models a match played"""
    players = db.ListProperty(str)
    scores = db.ListProperty(int)
    elo_delta = db.IntegerProperty()
    duration = db.IntegerProperty()
    
    played = db.DateTimeProperty(auto_now_add=True)
    