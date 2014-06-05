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
      ret = d.blockchain_certify()
      sender_address = "manuelaraoz@gmail.com"
      subject = "Document certified: %s %s" % (ret['success'], d.digest)
      body = subject + "\n\nmesage: %s" % (ret['message'])
      mail.send_mail(sender_address, ADMIN_EMAIL, subject, body)

