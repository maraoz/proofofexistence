import webapp2

from model import Document
from blockchain import publish_data, do_check_document, publish_data_old
from base import JsonAPIHandler

class BootstrapHandler(JsonAPIHandler):
  def handle(self):
    return {"success" : True}

class PendingHandler(webapp2.RequestHandler):
  def get(self):
    pending = Document.get_pending()
    url = SECRET_ADMIN_PATH + '/autopay'
    for d in pending:
      self.response.write('<a href="%s?d=%s">%s</a><br /><br />' % (url, d.digest, d.digest))

class AutopayHandler(JsonAPIHandler):
  def handle(self):
    digest = self.request.get("d")
    doc = Document.get_doc(digest)
    if not doc or not doc.tx:
      return {"success" : False, "error": "format"}
    # TODO: add check to prevent double timestamping
    tx, message = publish_data_old(doc)
    do_check_document(digest)
    return {"success" : True, "tx" : tx, "message" : message}


class BasePaymentCallback(JsonAPIHandler):
  def handle(self):
    test = self.request.get("test") == "true"
    try:
      tx_hash = self.request.get("transaction_hash")
      address = self.request.get("address")
      satoshis = int(self.request.get("value"))
    except ValueError, e:
      return "error: value error"
    if not tx_hash:
      return "error: no transaction_hash"
                     
    if not address:
      return "error: no address"
                                                    
    if satoshis <= 0:  # outgoing payment
      return "*ok*"

    if not test:
      return self.process_payment(satoshis, digest) 
    return "*ok*"

  def process_payment(self, satoshis, digest):
    secret = self.request.get("secret")
    if len(digest) != 64 or not callback_secret_valid(secret) or satoshis < MIN_SATOSHIS_PAYMENT:
      return {"success" : False, "reason" : "format or payment below " + str(MIN_SATOSHIS_PAYMENT)}

    doc = Document.get_doc(digest)
    if not doc:
      return {"success" : False, "reason" : "Couldn't find document"}
    doc.pending = False
    doc.put()

    return {"success" : True}
  

class PaymentCallback(BasePaymentCallback):
  pass


