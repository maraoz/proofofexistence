import webapp2, jinja2, os, hashlib, logging, urllib
import json
import datetime

from model import Document
from blockchain import get_txs_for_addr, publish_data,\
  publish_data_old, new_address, callback_secret_valid

from base import JsonAPIHandler
from doc import DigestStoreHandler
from config import MIN_SATOSHIS_PAYMENT

class ExternalRegisterHandler(DigestStoreHandler):
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

    doc_dict = self.doc.to_dict()
    pay_address = doc_dict.get('payment_address')
    if not pay_address:
      return {"success" : False, "reason" : "cant generate pay address"}

    ret["pay_address"] = pay_address
    ret["price"] = MIN_SATOSHIS_PAYMENT
    return ret

class ExternalStatusHandler(JsonAPIHandler):
  def handle(self):
    digest = self.request.get("d")
    doc = Document.get_doc(digest)
    if not digest:
      return {"success": False, "reason": "format"}
    if not doc:
      return {"success": False, "reason": "nonexistent"}
    if doc.tx:
      return {"success": True, "status": "confirmed"}
    if doc.ladd and doc.radd:
      return {"success": True, "status": "pending"}

    return {"success": True, "status": "registered"}
