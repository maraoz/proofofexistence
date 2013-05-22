#!/usr/bin/env python


import webapp2, jinja2, os, hashlib
import json as json
import datetime
from embed import hide_in_address

from google.appengine.api import urlfetch
from google.appengine.ext import db

from model import DocumentProof

SECRET = "INSERT HERE"


MIN_SATOSHIS = 0.005 * 100000000 
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


class RegisterHandler(JsonAPIHandler):
    def handle(self):
        document = self.request.get("d")
        if not document:
            return {"success" : False, "reason" : "format"}
        digest = hash_digest(document)
        
        docproof = DocumentProof.all().filter("digest = ", digest).get()
        if docproof:
            return {"success" : False, "reason": "existing", "digest": digest, "args": [export_timestamp(docproof), digest]}
        
        docproof = DocumentProof(digest=digest)
        docproof.put()
        
        return {"success": True, "digest": digest}
    
class LatestHandler(JsonAPIHandler):
    def handle(self):
        latest = DocumentProof.all().order("-timestamp").run(limit=5)
        return [{"digest":doc.digest, "timestamp":export_timestamp(doc)} for doc in latest]
    
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
        url = "http://blockchain.info/address/%s?format=json&limit=5" % (addr)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            j = json.loads(result.content)
            return [tx["hash"] for tx in j["txs"]]
        else:
            return None
        
    def handle(self):
        digest = self.request.get("d")
        doc = DocumentProof.all().filter("digest = ", digest).get()
        if not doc or not doc.ladd or not doc.radd or doc.tx:
            return {"success" : False, "error": "format"}
        
        ltxs = self.get_txs(doc.ladd)
        rtxs = self.get_txs(doc.radd)
        if not ltxs or not rtxs:
            return {"success" : False, "error": "no transactions" + str(ltxs) + str(rtxs)}
        intersection = [tx for tx in ltxs if tx in rtxs]
        if len(intersection) == 0:
            return {"success" : False, "error": "no intersecting"}
        doc.tx = intersection[0]
        doc.put()
        return {"success" : True, "tx" : doc.tx}

app = webapp2.WSGIApplication([
    ('/api/register', RegisterHandler),
    ('/api/latest', LatestHandler),
    ('/api/detail', DetailHandler),
    ('/api/callback', PaymentCallback),
    ('/api/check', CheckHandler)
], debug=False)

