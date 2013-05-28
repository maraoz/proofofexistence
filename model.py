
from google.appengine.ext import db

class DocumentProof(db.Model):
    """Models a proof of document existence at a certain time"""
    digest = db.StringProperty()
    ladd = db.StringProperty()
    radd = db.StringProperty()
    tx = db.StringProperty()
    
    timestamp = db.DateTimeProperty(auto_now_add=True)
    blockstamp = db.DateTimeProperty()

class LatestConfirmedDocuments(db.Model):
    """Helper table for latest confirmed documents retrieval"""
    
    digests = db.ListProperty(db.Key)
    
    @classmethod
    def get_inst(cls):
        inst = cls.all().get()
        if not inst:
            inst = cls()
            inst.put()
        return inst
    