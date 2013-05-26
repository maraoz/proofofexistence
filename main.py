#!/usr/bin/env python


import webapp2, jinja2, os, hashlib, logging
import json as json
import datetime
from embed import hide_in_address

from google.appengine.api import urlfetch
from google.appengine.ext import db

from model import DocumentProof

SECRET = "INSERT HERE"


DONATION_ADDRESS = "17Ab2P14CJ7FMJF6ARVQ7oVrA3iA5RFP6G"
BTC_TO_SATOSHI = 100000000
MIN_SATOSHIS = 0.005 * BTC_TO_SATOSHI
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


def hash_digest(x):
    hasher = hashlib.new('SHA256')
    hasher.update(x)
    return hasher.hexdigest()

def export_timestamp(doc):
    return doc.timestamp.strftime("%Y-%m-%d %H:%M:%S")

class JsonAPIHandler(webapp2.RequestHandler):
    def post(self):
        self.get()
    def get(self):
        resp = self.handle()
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        self.response.write(json.dumps(resp, default=dthandler))


class DigestStoreHandler(JsonAPIHandler):
    def store_digest(self, digest):
        docproof = DocumentProof.all().filter("digest = ", digest).get()
        if docproof:
            return {"success" : False, "reason": "existing", "digest": digest, "args": [export_timestamp(docproof)]}
        
        docproof = DocumentProof(digest=digest)
        docproof.put()
        
        return {"success": True, "digest": digest}
 
class UploadHandler(DigestStoreHandler):    
    def handle(self):
        document = self.request.get("d")
        if not document:
            return {"success" : False, "reason" : "format"}
        digest = hash_digest(document)
        
        return self.store_digest(digest)

class RegisterHandler(DigestStoreHandler):
    def handle(self):
        digest = self.request.get("d") #expects client-side hashing
        if not digest or len(digest) != 64:
            return {"success" : False, "reason" : "format"}
        
        return self.store_digest(digest)
    

class LatestHandler(JsonAPIHandler):
    def handle(self):
        confirmed = self.request.get("confirmed")
        query = DocumentProof.all()
        if confirmed and confirmed == "true":
            query = query.filter("tx !=", None).order("tx")
        latest = query.order("-timestamp").run(limit=5)
        return [{"digest":doc.digest, "timestamp":export_timestamp(doc), "tx": doc.tx} for doc in latest]
    
class DetailHandler(JsonAPIHandler):
    def handle(self):
        digest = self.request.get("d")
        doc = DocumentProof.all().filter("digest = ", digest).get()
        if not doc:
            return {"success" : False}
        return {
            "success": True,
            "digest":doc.digest,
            "timestamp":export_timestamp(doc),
            "ladd": doc.ladd,
            "radd": doc.radd,
            "tx" : doc.tx
        }

class PaymentCallback(JsonAPIHandler):
    def handle(self):
        j = json.loads(self.request.body)  # json["order"]["custom"]
        order = j["order"]
        d = order["custom"]
        satoshis = order["total_btc"]["cents"]
        
        secret = self.request.get("secret")
        if len(d) != 64 or secret != SECRET or satoshis < MIN_SATOSHIS:
            return {"success" : False, "reason" : "format or payment below " + str(MIN_SATOSHIS)}
        
        doc = DocumentProof.all().filter("digest = ", d).get()
        if not doc:
            return {"success" : False, "reason" : "Couldnt find document"}
        
        reduced = d.decode('hex')  # 32 bytes
        left = bytes(reduced[:20])
        right = bytes(reduced[20:] + "\0"*8)
        
        ladd = hide_in_address(left)
        radd = hide_in_address(right)
        
        doc.ladd = ladd
        doc.radd = radd
        doc.put()
        
        return {"success" : True, "addrs" : [doc.ladd, doc.radd]}

class CheckHandler(JsonAPIHandler):
    def get_txs(self, addr):
        url = "https://blockchain.info/address/%s?format=json&limit=5" % (addr)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return [tx["hash"] for tx in j["txs"]]
        else:
            logging.error("Error accessing blockchain API: "+result.status_code)
            return None
        
    def handle(self):
        digest = self.request.get("d")
        doc = DocumentProof.all().filter("digest = ", digest).get()
        if not doc or not doc.ladd or not doc.radd or doc.tx:
            return {"success" : False, "error": "format"}
        
        ltxs = self.get_txs(doc.ladd)
        rtxs = self.get_txs(doc.radd)
        if not ltxs or not rtxs:
            return {"success" : False, "error": "no transactions"}
        intersection = [tx for tx in ltxs if tx in rtxs]
        if len(intersection) == 0:
            return {"success" : False, "error": "no intersecting"}
        doc.tx = intersection[0]
        doc.put()
        return {"success" : True, "tx" : doc.tx}

class PendingHandler(JsonAPIHandler):
    def handle(self):
        pending = DocumentProof.all().filter("ladd != ", None).filter("tx =", None).run()
        return [d.digest for d in pending]

class WidgetJSHandler(webapp2.RequestHandler):
    def get_info(self):
        url = "https://blockchain.info/address/%s?format=json" % (DONATION_ADDRESS)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return (j["n_tx"], j["total_received"]/float(BTC_TO_SATOSHI))
        else:
            logging.error("Error accessing blockchain API: "+result.status_code)
            return None
    def get(self):
        counter, amount = self.get_info()
        self.response.write("""
        setTimeout(function(){
            CoinWidget.build({
                'counter': %d,
                'amount': %f,
                'cache': 0
            },1);
        },300);
        """ % (counter, amount))

app = webapp2.WSGIApplication([
    ('/api/register', RegisterHandler),
    ('/api/upload', UploadHandler),
    ('/api/latest', LatestHandler),
    ('/api/detail', DetailHandler),
    ('/api/callback', PaymentCallback),
    ('/api/check', CheckHandler),
    ('/api/pending', PendingHandler),
    ('/api/widget.js', WidgetJSHandler)
], debug=False)

