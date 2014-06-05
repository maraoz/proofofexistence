
from google.appengine.ext import db
from pycoin.encoding import hash160_sec_to_bitcoin_address
from blockchain import new_address, publish_data
import datetime

class LatestBlockchainDocuments(db.Model):
  """Helper table for latest confirmed documents retrieval"""
  digests = db.StringListProperty()
  
  def add_document(self, digest):
    self.digests = [digest] + self.digests[:-1]
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
  payment_address = db.StringProperty()

  timestamp = db.DateTimeProperty(auto_now_add=True)
  txstamp = db.DateTimeProperty()
  blockstamp = db.DateTimeProperty()
  
  legacy = db.BooleanProperty()

  def payment_received(self):
    return not self.pending

  def is_actionable(self):
    return self.payment_received() and self.tx == ''

  def to_dict(self):
    if not self.payment_address:
      self.payment_address = new_address(self.digest)
      self.put()
    d = db.to_dict(self)
    return d

  def confirmed(self, tx_hash, tx_timestamp):
    self.tx = tx_hash
    self.txstamp = datetime.datetime.fromtimestamp(tx_timestamp)
    self.pending = False
    self.put()

  @classmethod
  def get_doc(cls, digest):
    return cls.all().filter("digest = ", digest).get()

  @classmethod
  def get_by_address(cls, address):
    return cls.all().filter('payment_address = ', address).get()

  @classmethod
  def new(cls, digest):
    d = cls(digest=digest)
    d.pending = True
    d.legacy = False
    d.tx = ''
    d.payment_address = None

    d.put()
    return d

  @classmethod
  def import_legacy(cls, digest, tx, timestamp, txstamp):
    d = cls.new(digest)
    d.pending = False
    d.legacy = True
    d.tx = tx
    d.timestamp = timestamp
    d.txstamp = txstamp
    d.payment_address = 'coinbase'

    d.put()
    return d

  LATEST_N = 5
  @classmethod
  def get_latest(cls, confirmed=False):
    if confirmed:
      bag = LatestBlockchainDocuments.get_inst()
      return [cls.get_doc(digest) for digest in bag.digests]
    else:
      return cls.all().order("-timestamp").run(limit=cls.LATEST_N)

  @classmethod
  def get_actionable(cls):
    return cls.all().filter("pending == ", False).filter("tx == ", '').run()

  def blockchain_certify(self):
    if self.tx:
      return {"success" : False, "error": "already certified"}
    # TODO: add check to prevent double timestamping
    txid, message = publish_data(self.digest.decode('hex'))
    if txid:
      self.tx = txid
      self.txstamp = datetime.datetime.now()
      LatestBlockchainDocuments.get_inst().add_document(digest)
      self.put()
    return {"success" : txid is not None, "tx" : txid, "message" : message}


