import webapp2, jinja2, os, hashlib, logging, urllib
import json
import datetime

from model import Document
from google.appengine.api import mail

from secrets import ADMIN_EMAIL
from blockchain import auto_consolidate
class ConsolidationCron(webapp2.RequestHandler):
  def get(self):
    archiveable = Document.get_archiveable()
    processed = False
    for d in archiveable:
      res = d.archive()
      self.response.write("%s %s<br />" % (d.digest, res))
      processed = True
    if processed:
      self.response.write("Running autoconsolidate<br />")
      auto_consolidate()
    else:
      self.response.write("Finished without operation<br />")

class ConfirmationCron(webapp2.RequestHandler):
  def get(self):
    actionable = Document.get_actionable()
    for d in actionable:
      ret = d.blockchain_certify()
      sender_address = "manuelaraoz@gmail.com"
      subject = "Document certified: %s %s" % (ret['success'], d.digest)
      body = subject + "\n\nmesage: %s" % (ret['message'])
      mail.send_mail(sender_address, ADMIN_EMAIL, subject, body)

