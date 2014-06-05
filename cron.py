import webapp2, jinja2, os, hashlib, logging, urllib
import json
import datetime

from model import Document
from google.appengine.api import mail

from secrets import ADMIN_EMAIL

class ConfirmationCron(webapp2.RequestHandler):
  def get(self):
    actionable = Document.get_actionable()
    for d in actionable:
      ret = doc.blockchain_certify()
      sender_address = "Proof of Existence <system@proofofexistence.com>"
      subject = "Document certified: %s %s" % (ret.success, d.digest)
      body = subject
      mail.send_mail(sender_address, ADMIN_EMAIL, subject, body)

