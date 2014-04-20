import webapp2, jinja2, os, hashlib, logging, urllib
import json
import datetime

from model import Document
from blockchain import get_txs_for_addr

from base import export_timestamp
from base import JsonAPIHandler

from config import MIN_SATOSHIS_PAYMENT


def hash_digest(x):
  hasher = hashlib.new('SHA256')
  hasher.update(x)
  return hasher.hexdigest()

class LatestDocumentsHandler(JsonAPIHandler):
  def handle(self):
    confirmed = self.request.get("confirmed")
    confirmed = confirmed and confirmed == "true"

    return [doc.to_dict() for doc in Document.get_latest(confirmed)]

class DigestStoreHandler(JsonAPIHandler):
  def store_digest(self, digest):
    old_doc = Document.get_doc(digest)
    if old_doc:
      return {"success" : False, "reason": "existing",
       "digest": digest, "args": [export_timestamp(old_doc.timestamp)]}

    d = Document.new(digest)
    self.doc = d # don't remove, needed for API
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

class DocumentPaymentHandler(JsonAPIHandler):
  def handle(self):
    digest = self.request.get("d")
    doc = Document.get_doc(digest)
    if not doc:
      return {"success" : False, "error": "Document not found"}
    return {"success": True, "payment": doc.payment_received()}

class DocumentGetHandler(JsonAPIHandler):
  def handle(self):
    digest = self.request.get("d")
    doc = Document.get_doc(digest)
    if not doc:
      return {"success" : False, "error": "Document not found"}
    return {"success": True, "doc": doc.to_dict()}

class DocumentCheckHandler(JsonAPIHandler):
  def handle(self):
    digest = self.request.get("d")
    doc = Document.get_doc(digest)
    if not doc or not doc.payment_address:
      return {"success" : False, "error": "format"}
    
    if not doc.tx:
      return {"success" : False, "error": "no transaction"}

    return {"success" : True, "tx" : doc.tx}
