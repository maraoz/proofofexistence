
from google.appengine.ext import db

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


class DocumentProof(db.Model):
    """Models a proof of document existence at a certain time"""
    digest = db.StringProperty()
    ladd = db.StringProperty()
    radd = db.StringProperty()
    tx = db.StringProperty()

    timestamp = db.DateTimeProperty(auto_now_add=True)
    blockstamp = db.DateTimeProperty()

    def to_dict(self):
        d = db.to_dict(self)
        return d

    @classmethod
    def get_doc(cls, digest):
        return cls.all().filter("digest = ", digest).get()

    @classmethod
    def new(cls, digest):
        d = cls(digest=digest)
        d.put()
        return d

    LATEST_N = 5
    @classmethod
    def get_latest(cls, confirmed=False):
        if confirmed:
            bag = LatestConfirmedDocuments.get_inst()
            return DocumentProof.get(bag.digests)
        else:
            return DocumentProof.all().order("-timestamp").run(limit=cls.LATEST_N)

    @classmethod
    def pending(cls):
        return cls.all().filter("ladd != ", None).filter("tx =", None).run()


