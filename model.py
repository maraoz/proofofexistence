
from google.appengine.ext import db

class DocumentProof(db.Model):
    """Models a proof of document existence at a certain time"""
    digest = db.StringProperty()
    ladd = db.StringProperty()
    radd = db.StringProperty()
    tx = db.StringProperty()
    
    timestamp = db.DateTimeProperty(auto_now_add=True)

class LatestConfirmedDocuments(db.Model):
    """Helper table for latest confirmed documents retrieval"""
    
    digests = db.ListProperty()
