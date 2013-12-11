#!/usr/bin/env python


import webapp2, jinja2, os, hashlib, logging, urllib
import json as json
import datetime

from google.appengine.api import urlfetch

from model import DocumentProof, LatestConfirmedDocuments
from coinbase import CoinbaseAccount
from secrets import CALLBACK_SECRET, BLOCKCHAIN_WALLET_GUID, \
    BLOCKCHAIN_PASSWORD_1, BLOCKCHAIN_PASSWORD_2, COINBASE_API_KEY,\
    SECRET_ADMIN_PATH



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

        docproof = DocumentProof.get_doc(digest)
        if docproof:
            return {"success" : False, "reason": "existing", "digest": digest, "args": [export_timestamp(docproof.timestamp)]}

        d = DocumentProof.new(digest)
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

        return [doc.to_dict() for doc in DocumentProof.get_latest(confirmed)]

class DocumentGetHandler(JsonAPIHandler):
    def handle(self):
        digest = self.request.get("d")
        doc = DocumentProof.get_doc(digest)
        if not doc:
            return {"success" : False}
        return {"success": True, "doc": doc.to_dict()}

class BasePaymentCallback(JsonAPIHandler):
    def process_payment(self, satoshis, digest):
        secret = self.request.get("secret")
        if len(digest) != 64 or secret != CALLBACK_SECRET or satoshis < MIN_SATOSHIS_PAYMENT:
            return {"success" : False, "reason" : "format or payment below " + str(MIN_SATOSHIS_PAYMENT)}

        doc = DocumentProof.get_doc(digest)
        if not doc:
            return {"success" : False, "reason" : "Couldnt find document"}

        reduced = digest.decode('hex')  # 32 bytes
        left = bytes(reduced[:20])
        right = bytes(reduced[20:] + "\0"*8)

        ladd = hide_in_address(left)
        radd = hide_in_address(right)

        doc.ladd = ladd
        doc.radd = radd
        doc.put()

        return {"success" : True, "addrs" : [doc.ladd, doc.radd]}

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
    def get_txs(self, addr):
        url = "https://blockchain.info/address/%s?format=json&limit=5" % (addr)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return [(tx["hash"], tx["time"]) for tx in j["txs"]]
        else:
            logging.error("Error accessing blockchain API: " + str(result.status_code))
            return None

    def handle(self):
        digest = self.request.get("d")
        doc = DocumentProof.get_doc(digest)
        if not doc or not doc.ladd or not doc.radd or doc.tx:
            return {"success" : False, "error": "format"}

        ltxs = self.get_txs(doc.ladd)
        rtxs = self.get_txs(doc.radd)
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
        pending = DocumentProof.pending()
        for d in pending:
            self.response.write('<a href="/api/autopay?d=%s">%s</a><br /><br />' % (d.digest, d.digest))

class AutopayHandler(JsonAPIHandler):
    def has_txs(self, addr):
        url = "http://blockchain.info/address/%s?format=json&limit=1" % (addr)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return len(j["txs"]) > 0
        else:
            logging.error("Error accessing blockchain API: " + str(result.status_code))
            return True

    def do_check(self, d):
        url = "http://www.proofofexistence.com/api/check?d=%s" % (d)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return j["success"]
        else:
            logging.error("Error accessing our own API: " + str(result.status_code))
            return None

    def do_pay(self, d, ladd, radd):
        recipients = json.dumps({
                             ladd : SATOSHI,
                             radd: SATOSHI
                                 }, separators=(',', ':'))
        note_encode = urllib.urlencode({"note":"http://www.proofofexistence.com/detail/" + d})
        data = (BLOCKCHAIN_WALLET_GUID, BLOCKCHAIN_PASSWORD_1, BLOCKCHAIN_PASSWORD_2, recipients, BLOCKCHAIN_FEE, POE_PAYMENTS_ADDRESS, note_encode)
        url = 'https://blockchain.info/merchant/%s/sendmany?password=%s&second_password=%s&recipients=%s&shared=false&fee=%d&from=%s&%s' % data
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return (j["message"], j["tx_hash"])
        else:
            logging.error("Error accessing blockchain API: " + str(result.status_code))
            return (None, None)

    def handle(self):
        digest = self.request.get("d")
        doc = DocumentProof.get_doc(digest)
        if not doc or not doc.ladd or not doc.radd or doc.tx:
            return {"success" : False, "error": "format"}
        if self.has_txs(doc.ladd):
            return {"success" : False, "error": "ladd"}
        if self.has_txs(doc.radd):
            return {"success" : False, "error": "radd"}
        message, tx = self.do_pay(doc.digest, doc.ladd, doc.radd)
        self.do_check(digest)
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
        doc = DocumentProof.get_doc(digest)
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
    (SECRET_ADMIN_PATH+'/bootstrap', BootstrapHandler),
    
    # callbacks
    ('/api/callback', PaymentCallback),
    ('/api/api_callback', ApiPaymentCallback),

    # public API
    ('/api/v1/register', ExternalRegisterHandler),
    ('/api/v1/status', ExternalStatusHandler)
], debug=False)

