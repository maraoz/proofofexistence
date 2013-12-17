#!/usr/bin/env python


import webapp2, jinja2, os, hashlib, logging, urllib
import json as json
import datetime

from google.appengine.api import urlfetch

from model import Document, LatestConfirmedDocuments
from coinbase import CoinbaseAccount
from secrets import CALLBACK_SECRET, BLOCKCHAIN_WALLET_GUID, \
    BLOCKCHAIN_PASSWORD_1, BLOCKCHAIN_PASSWORD_2, COINBASE_API_KEY,\
    SECRET_ADMIN_PATH
from blockchain import get_txs_for_addr, has_txs, get_encrypted_wallet,\
    decrypt_wallet, publish_data, publish_data_old, do_check_document



BTC_TO_SATOSHI = 100000000
BLOCKCHAIN_FEE = int(0.0001 * BTC_TO_SATOSHI)

DONATION_ADDRESS = "17Ab2P14CJ7FMJF6ARVQ7oVrA3iA5RFP6G"
POE_PAYMENTS_ADDRESS = "11xP3sjdQy4QgP47RNHLH6DnKXWWVfb6B"
SATOSHI = 1
MIN_SATOSHIS_PAYMENT = int(0.005 * BTC_TO_SATOSHI)
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


def hash_digest(x):
    hasher = hashlib.new('SHA256')
    hasher.update(x)
    return hasher.hexdigest()

def export_timestamp(timestamp):
    if not timestamp:
        return None
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


class StaticHandler(webapp2.RequestHandler):
    def get(self, _):
        name = self.request.path.split("/")[1]
        if name == "":
            name = "index"

        values = {
            "name": name
        }

        try:
            self.response.write(JINJA_ENVIRONMENT.get_template("templates/" + name + '.html').render(values))
        except IOError, e:
            self.error(404)
            self.response.write("404: %s not found! %s" % (name, e))


class JsonAPIHandler(webapp2.RequestHandler):
    def post(self):
        self.get()

    def get(self):
        resp = self.handle()
        self.response.headers['Content-Type'] = "application/json"
        dthandler = lambda obj: export_timestamp(obj) if isinstance(obj, datetime.datetime) else None
        self.response.write(json.dumps(resp, default=dthandler))


class DigestStoreHandler(JsonAPIHandler):
    def store_digest(self, digest):

        docproof = Document.get_doc(digest)
        if docproof:
            return {"success" : False, "reason": "existing", "digest": digest, "args": [export_timestamp(docproof.timestamp)]}

        d = Document.new(digest)
        return {"success": True, "digest": d.digest}

class DocumentUploadHandler(DigestStoreHandler):
    def handle(self):
        d = self.request.get("d")  # full document
        if not d:
            return {"success" : False, "reason" : "format"}
        digest = hash_digest(d)

        return self.store_digest(digest)

class DocumentRegisterHandler(DigestStoreHandler):
    def handle(self):
        digest = self.request.get("d")  # expects client-side hashing
        if not digest or len(digest) != 64:
            return {"success" : False, "reason" : "format"}

        return self.store_digest(digest)

class BootstrapHandler(JsonAPIHandler):
    def handle(self):
        return {"success" : True}

class LatestDocumentsHandler(JsonAPIHandler):
    def handle(self):
        confirmed = self.request.get("confirmed")
        confirmed = confirmed and confirmed == "true"

        return [doc.to_dict() for doc in Document.get_latest(confirmed)]

class DocumentGetHandler(JsonAPIHandler):
    def handle(self):
        digest = self.request.get("d")
        doc = Document.get_doc(digest)
        if not doc:
            return {"success" : False}
        return {"success": True, "doc": doc.to_dict()}

class BasePaymentCallback(JsonAPIHandler):
    def process_payment(self, satoshis, digest):
        secret = self.request.get("secret")
        if len(digest) != 64 or secret != CALLBACK_SECRET or satoshis < MIN_SATOSHIS_PAYMENT:
            return {"success" : False, "reason" : "format or payment below " + str(MIN_SATOSHIS_PAYMENT)}

        doc = Document.get_doc(digest)
        if not doc:
            return {"success" : False, "reason" : "Couldnt find document"}
        #reduced = digest.decode('hex')  # 32 bytes
        doc.pending = False
        doc.put()

        return {"success" : True}

class PaymentCallback(BasePaymentCallback):
    def handle(self):
        j = json.loads(self.request.body)
        order = j["order"]
        digest = order["custom"]
        satoshis = order["total_btc"]["cents"]
        return self.process_payment(satoshis, digest)

class ApiPaymentCallback(BasePaymentCallback):
    def handle(self):
        j = json.loads(self.request.body)
        satoshis = int(j["amount"] * BTC_TO_SATOSHI)
        digest = self.request.get("d")
        return self.process_payment(satoshis, digest)



class DocumentCheckHandler(JsonAPIHandler):
    def handle(self):
        digest = self.request.get("d")
        doc = Document.get_doc(digest)
        if not doc or not doc.ladd or not doc.radd or doc.tx:
            return {"success" : False, "error": "format"}

        ltxs = get_txs_for_addr(doc.ladd)
        rtxs = get_txs_for_addr(doc.radd)
        if not ltxs or not rtxs:
            return {"success" : False, "error": "no transactions"}
        intersection = [tx for tx in ltxs if tx in rtxs]
        if len(intersection) == 0:
            return {"success" : False, "error": "no intersecting"}

        doc.tx = intersection[0][0]
        doc.blockstamp = datetime.datetime.fromtimestamp(intersection[0][1])
        doc.put()

        bag = LatestConfirmedDocuments.get_inst()
        bag.digests = [doc.key()] + bag.digests[:-1]
        bag.put()

        return {"success" : True, "tx" : doc.tx}

class PendingHandler(webapp2.RequestHandler):
    def get(self):
        pending = Document.get_pending()
        url = SECRET_ADMIN_PATH+'/autopay'
        for d in pending:
            self.response.write('<a href="%s?d=%s">%s</a><br /><br />' % (url, d.digest, d.digest))

class AutopayHandler(JsonAPIHandler):
    def handle(self):
        digest = self.request.get("d")
        doc = Document.get_doc(digest)
        if not doc or not doc.tx:
            return {"success" : False, "error": "format"}
        # TODO: add check to prevent double timestamping
        tx, message = publish_data(doc.digest.decode("hex"))
        do_check_document(digest)
        return {"success" : True, "tx" : tx, "message" : message}

class ExternalRegisterHandler(DigestStoreHandler):

    def get_pay_address(self, d):
        account = CoinbaseAccount(api_key=COINBASE_API_KEY)
        callback_url = "https://www.proofofexistence.com/api/api_callback?secret=%s&d=%s" % (CALLBACK_SECRET, d)
        return account.generate_receive_address(callback_url).get("address")

    def handle(self):
        digest = self.request.get("d")  # expects client-side hashing

        if not digest or len(digest) != 64:
            return {"success" : False, "reason" : "format"}
        try:
            digest.decode("hex")
        except TypeError:
            return {"success" : False, "reason" : "format"}

        ret = self.store_digest(digest)
        if not ret["success"]:
            del ret["args"]
            return ret

        pay_address = self.get_pay_address(digest)
        if not pay_address:
            return {"success" : False, "reason" : "cant generate pay address"}

        ret["pay_address"] = pay_address
        ret["price"] = MIN_SATOSHIS_PAYMENT
        return ret



class ExternalStatusHandler(JsonAPIHandler):
    def handle(self):
        digest = self.request.get("d")
        doc = Document.get_doc(digest)
        if not digest:
            return {"success": False, "reason": "format"}
        if not doc:
            return {"success": False, "reason": "nonexistent"}
        if doc.tx:
            return {"success": True, "status": "confirmed"}
        if doc.ladd and doc.radd:
            return {"success": True, "status": "pending"}

        return {"success": True, "status": "registered"}

app = webapp2.WSGIApplication([
    # static files 
    ('/((?!api).)*', StaticHandler),
    
    # internal API
    ('/api/document/register', DocumentRegisterHandler),
    ('/api/document/upload', DocumentUploadHandler),
    ('/api/document/latest', LatestDocumentsHandler),
    ('/api/document/get', DocumentGetHandler),
    ('/api/document/check', DocumentCheckHandler),
    
    # manual admin
    (SECRET_ADMIN_PATH+'/pending', PendingHandler),
    (SECRET_ADMIN_PATH+'/autopay', AutopayHandler),
    ('/api/bootstrap', BootstrapHandler),
    
    # callbacks
    ('/api/callback', PaymentCallback),
    ('/api/api_callback', ApiPaymentCallback),

    # public API
    ('/api/v1/register', ExternalRegisterHandler),
    ('/api/v1/status', ExternalStatusHandler)
], debug=False)

