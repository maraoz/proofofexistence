#!/usr/bin/env python


import webapp2, json, jinja2, os, hashlib

from google.appengine.ext import db

from model import DocumentProof

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def hash_digest(x):
    hasher = hashlib.new('SHA512')
    hasher.update(x)
    return hasher.hexdigest()

class JsonAPIHandler(webapp2.RequestHandler):
    def post(self):
        self.get()
    def get(self):
        resp = self.handle()
        self.response.write(json.dumps(resp))


class RegisterHandler(JsonAPIHandler):
    def handle(self):
        document = self.request.get("d")
        dig = hash_digest(document)
        return {"dig": dig}
"""        
        if not username or not password:
            return {"success": False , "error": "format"}
        
        same_name = Player.all().filter('username =', username)
        if same_name.get():
            return {"success": False , "error": "username"}
        
        
        player = Player(username=username, password=hash_digest(password), searching = False, match_server = None)
        player.put()
        return {"success": True}
"""

app = webapp2.WSGIApplication([
    ('/api/register', RegisterHandler),
    
], debug=False)

