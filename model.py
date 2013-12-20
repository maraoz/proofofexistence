
from google.appengine.ext import db
from pycoin.encoding import hash160_sec_to_bitcoin_address
from appengine._internal.django.utils.datetime_safe import datetime

class LatestConfirmedDocuments(db.Model):
    """Helper table for latest confirmed documents retrieval"""
    digests = db.ListProperty(db.Key)
    
    def add_document(self, doc):
        self.digests = [doc.key()] + self.digests[:-1]
        self.put()
    
    @classmethod
    def get_inst(cls):
        inst = cls.all().get()
        if not inst:
            inst = cls()
            inst.put()
        return inst


class Document(db.Model):
    """Models a proof of document existence at a certain time"""
    digest = db.StringProperty()
    pending = db.BooleanProperty()
    tx = db.StringProperty()

    timestamp = db.DateTimeProperty(auto_now_add=True)
    blockstamp = db.DateTimeProperty()

    def to_dict(self):
        d = db.to_dict(self)
        return d

    def get_address_repr(self):
        data = self.digest.decode("hex")
        lpart = data[:20]
        rpart = data[20:] + ("\x00" * 8)
        return [hash160_sec_to_bitcoin_address(part) for part in [lpart, rpart]]

    def confirmed(self, tx_hash, tx_timestamp):
        self.tx = tx_hash
        self.blockstamp = datetime.datetime.fromtimestamp(tx_timestamp)
        self.put()

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
            return cls.get(bag.digests)
        else:
            return cls.all().order("-timestamp").run(limit=cls.LATEST_N)

    @classmethod
    def get_pending(cls):
        return cls.all().filter("pending == ", True).run()


