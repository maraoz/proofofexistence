#!/usr/bin/env python


import webapp2, jinja2, os, hashlib
import json as json
import datetime
from coinbase import CoinbaseAccount
from embed import hide_in_address, recover_message

from google.appengine.ext import db

from model import DocumentProof

SECRET = "INSERT HERE"
COINBASE_API_KEY = "INSERT HERE"

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
        
        docproof = DocumentProof(digest=digest, in_blockchain=False)
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
        return {"success": True, "digest":doc.digest, "timestamp":export_timestamp(doc), "in_blockchain": doc.in_blockchain}

class PaymentCallback(JsonAPIHandler):
    def handle(self):
        """
        {
            "order": {
                "id": "5RTQNACF",
                "created_at": "2012-12-09T21:23:41-08:00",
                "status": "completed",
                "total_btc": {
                    "cents": 100000000,
                    "currency_iso": "BTC"
                },
                "total_native": {
                    "cents": 1253,
                    "currency_iso": "USD"
                },
                "custom": "order1234",
                "button": {
                    "type": "buy_now",
                    "name": "Alpaca Socks",
                    "description": "The ultimate in lightweight footwear",
                    "id": "5d37a3b61914d6d0ad15b5135d80c19f"
                },
                "transaction": {
                    "id": "514f18b7a5ea3d630a00000f",
                    "hash": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
                    "confirmations": 0
                }
            }
        }
        """
        d = self.request.get("d") # json["order"]["custom"]
        secret = self.request.get("secret")
        if len(d) != 64 or secret != SECRET:
            return {"success" : False}
        
        account = CoinbaseAccount(api_key=COINBASE_API_KEY)
        
        reduced = d.decode('hex')  # 32 bytes
        left = bytes(reduced[:20])
        right = bytes(reduced[20:] + "\0"*8)
        
        ladd = hide_in_address(left)
        radd = hide_in_address(right)
        
        return {"success" : True, "sell" : account.buy_price(), "addrs" : [ladd, radd]}

app = webapp2.WSGIApplication([
    ('/api/register', RegisterHandler),
    ('/api/latest', LatestHandler),
    ('/api/detail', DetailHandler),
    ('/api/callback', PaymentCallback)
], debug=False)

