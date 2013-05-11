#!/usr/bin/env python


import webapp2, jinja2, os, hashlib
import json as json
import datetime

from google.appengine.ext import db

from model import DocumentProof

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def hash_digest(x):
    hasher = hashlib.new('SHA256')
    hasher.update(x)
    return hasher.hexdigest()

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
            return {"success" : False, "reason": "existing"}
        
        docproof = DocumentProof(digest=digest)
        docproof.put()
        
        return {"success": True, "digest": digest}
    
class LatestHandler(JsonAPIHandler):
    def handle(self):
        latest = DocumentProof.all().order("-timestamp").run(limit=10)
        return [{"digest":doc.digest, "timestamp":doc.timestamp.strftime("%Y-%m-%d %H:%M:%S")} for doc in latest]

app = webapp2.WSGIApplication([
    ('/api/register', RegisterHandler),
    ('/api/latest', LatestHandler)
    
], debug=False)

