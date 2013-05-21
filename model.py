
from google.appengine.ext import db

class DocumentProof(db.Model):
    """Models a proof of document existence at a certain time"""
    digest = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    in_blockchain = db.BooleanProperty()
    
