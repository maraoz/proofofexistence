import webapp2

from base import export_timestamp, StaticHandler
from doc import DocumentRegisterHandler, DocumentUploadHandler, \
  LatestDocumentsHandler, DocumentGetHandler, DocumentPaymentHandler, \
  DocumentCheckHandler
from admin import PendingHandler, AutopayHandler, BootstrapHandler, \
  PaymentCallback
from api import ExternalRegisterHandler, ExternalStatusHandler
from secrets import SECRET_ADMIN_PATH
from cron import ConfirmationCron

app = webapp2.WSGIApplication([
  # static files
  ('/((?!api).)*', StaticHandler),

  # internal API
  ('/api/document/register', DocumentRegisterHandler),
  ('/api/document/upload', DocumentUploadHandler),
  ('/api/document/latest', LatestDocumentsHandler),
  ('/api/document/get', DocumentGetHandler),
  ('/api/document/payment', DocumentPaymentHandler),
  ('/api/document/check', DocumentCheckHandler),

  # manual admin
  (SECRET_ADMIN_PATH + '/pending', PendingHandler),
  (SECRET_ADMIN_PATH + '/autopay', AutopayHandler),
  (SECRET_ADMIN_PATH + '/bootstrap', BootstrapHandler),

  # callbacks for blockchain.info
  ('/api/callback', PaymentCallback),

  # public API
  ('/api/v1/register', ExternalRegisterHandler),
  ('/api/v1/status', ExternalStatusHandler),

  # cron
  ('/tasks/confirmation', ConfirmationCron)
], debug=True)
