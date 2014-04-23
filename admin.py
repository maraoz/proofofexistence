import webapp2
import datetime

from model import Document, LatestBlockchainDocuments
from blockchain import publish_data, callback_secret_valid
from base import JsonAPIHandler
from secrets import SECRET_ADMIN_PATH
from config import MIN_SATOSHIS_PAYMENT

class BootstrapHandler(JsonAPIHandler):
  def handle(self):
    d = self.request.get('d')
    tx = self.request.get('tx')
    ts = self.request.get('ts')
    txts = self.request.get('txts')
    doc = Document.import_legacy(d, tx, ts, txts)
    if doc:
      return {"success" : True}
    return {"success" : False}

class PendingHandler(webapp2.RequestHandler):
  def get(self):
    actionable = Document.get_actionable()
    url = SECRET_ADMIN_PATH + '/autopay'
    for d in actionable:
      self.response.write('<a href="%s?d=%s">%s</a><br /><br />' % (url, d.digest, d.digest))

class AutopayHandler(JsonAPIHandler):
  def handle(self):
    digest = self.request.get("d")
    doc = Document.get_doc(digest)
    if not doc or doc.tx:
      return {"success" : False, "error": "format"}
    # TODO: add check to prevent double timestamping
    txid, message = publish_data(doc.digest.decode('hex'))
    if txid:
      doc.tx = txid
      LatestBlockchainDocuments.get_inst().add_document(digest)
      doc.put()
    return {"success" : txid is not None, "tx" : txid, "message" : message}


class BasePaymentCallback(JsonAPIHandler):
  def handle(self):
    test = self.request.get("test") == "true"
    try:
      tx_hash = self.request.get("transaction_hash")
      address = self.request.get("address")
      satoshis = int(self.request.get("value"))
      payment_address = self.request.get("input_address")
    except ValueError, e:
      return "error: value error"
    if not tx_hash:
      return "error: no transaction_hash"
                     
    if not address:
      return "error: no address"
                                                    
    if satoshis <= 0:  # outgoing payment
      return "*ok*"
    if satoshis < MIN_SATOSHIS_PAYMENT: # not enough
      return "*ok*"


    if not test:
      doc = Document.get_by_address(payment_address)
      if not doc:
        return "error: couldn't find document"
      return self.process_payment(satoshis, doc) 
    return "*ok*"

  def process_payment(self, satoshis, doc):
    secret = self.request.get("secret")
    if not callback_secret_valid(secret):
      return "error: secret invalid"

    doc.pending = False
    doc.txstamp = datetime.datetime.now()
    doc.put()

    return "*ok*"
  

class PaymentCallback(BasePaymentCallback):
  pass


