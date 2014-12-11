'''
Blockchain.info Python Client for the JSON Merchant API for Google App Engine.
'''

from google.appengine.api import urlfetch
import logging
import json
import base64
import urllib
from random import random
from Crypto.Cipher import AES
from pycoin.tx.script import tools
from pycoin.services import blockchain_info
from pycoin.encoding import wif_to_secret_exponent,\
  bitcoin_address_to_hash160_sec, hash160_sec_to_bitcoin_address
from pycoin.tx import UnsignedTx, SecretExponentSolver, TxOut
from secrets import BLOCKCHAIN_WALLET_GUID, BLOCKCHAIN_PASSWORD_1, BLOCKCHAIN_PASSWORD_2, CALLBACK_SECRET,\
  BLOCKCHAIN_ENCRYPTED_WALLET, PAYMENT_PRIVATE_KEY, PAYMENT_ADDRESS
from Crypto.Protocol.KDF import PBKDF2
import io
import binascii
from pycoin.tx.UnsignedTx import UnsignedTxOut
from pycoin.serialize import b2h

TX_FEES = 10000
BLOCKCHAIN_DUST = 5430
B2S = 100000000

default_pbkdf2_iterations = 10

# debugging
class Mock():
  status_code = 500
def mock(url):
  print url
  return Mock()

# uncomment to debug
# urlfetch.fetch = mock

def btc2satoshi(x):
  return int(x * B2S)

def satoshi2btc(x):
  return x / float(B2S)


BASE_BLOCKCHAIN_URL = 'https://blockchain.info'

def get_base_blockchain_url(command):
  url = BASE_BLOCKCHAIN_URL
  url += '/merchant/%s/%s?password=%s' % (BLOCKCHAIN_WALLET_GUID, command, BLOCKCHAIN_PASSWORD_1)
  if len(BLOCKCHAIN_PASSWORD_2) > 0:
    url += '&second_password=%s' % (BLOCKCHAIN_PASSWORD_2)
  return url

def new_address(label=None):
  url = get_base_blockchain_url('new_address')
  if label:
    url += '&label='+str(label)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    j = json.loads(result.content)
    if not j.get('address'):
        logging.error(result.content)
    return j['address']
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None


def archive_address(address):
  url = get_base_blockchain_url('archive_address')
  url += '&address=%s' % address
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content)
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None

def auto_consolidate(days=10):
  url = get_base_blockchain_url('auto_consolidate')
  url += '&days=%s' % days
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content)
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None

def address_balance(addr):
  url = BASE_BLOCKCHAIN_URL + '/address/%s?format=json&limit=0' % addr
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content)['final_balance']
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None

def payment(to, satoshis, _from=None):
  url = get_base_blockchain_url('payment')
  url += '&to=%s&amount=%s&shared=%s&fee=%s' % (to, int(satoshis), 'false', TX_FEES)
  if _from:
    url += '&from=%s' % (_from)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content).get('tx_hash')
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None


def do_check_document(d):
  # FIXME: don't do this plz!!
  url = 'http://www.proofofexistence.com/api/check?d=%s' % (d)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    j = json.loads(result.content)
    return j['success']
  else:
    logging.error('Error accessing our own API: ' + str(result.status_code))
    return None

def sendmany(recipient_list, _from=None):
  url = get_base_blockchain_url('sendmany')
  # can't do it using python dict because we have repeated addresses
  recipients = '{'
  for addr, satoshis in recipient_list:
    recipients += '\'%s\':%s,' % (addr, satoshis)
  recipients = recipients[:-1]
  recipients += '}'
  url += '&recipients=%s&shared=%s&fee=%s' % (recipients, 'false', TX_FEES)
  if _from:
    url += '&from=%s' % (_from)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    j = json.loads(result.content)
    return (j.get('tx_hash'), j.get('message'))
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None

def get_tx(tx_hash):
  url = BASE_BLOCKCHAIN_URL + '/rawtx/%s' % (tx_hash)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content)
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None
def get_block(height):
  if not height:
    return None
  url = BASE_BLOCKCHAIN_URL + '/block-height/%s?format=json' % (height)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content).get('blocks')[0]
  else:
    logging.error('There was an error contacting the Blockchain.info API')
    return None

def get_txs_for_addr(addr, limit=5):
  url = BASE_BLOCKCHAIN_URL + '/address/%s?format=json&limit=%s' % (addr, limit)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    j = json.loads(result.content)
    return [(tx['hash'], tx['time']) for tx in j['txs']]
  else:
    logging.error('Error accessing blockchain API: ' + str(result.status_code))
    return None

def has_txs(addr):
  return len(get_txs_for_addr(addr, 1)) > 0

def callback_secret_valid(secret):
  return secret == CALLBACK_SECRET

def get_encrypted_wallet(offline=True):
  if offline:
    return BLOCKCHAIN_ENCRYPTED_WALLET
  url = BASE_BLOCKCHAIN_URL + '/wallet/%s?format=%s' % (BLOCKCHAIN_WALLET_GUID, 'json')
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    j = json.loads(result.content)
    return j
  else:
    logging.error('Blockchain Error getting wallet from url %s, got result \n%d %s' % (url, result.status_code, result.content))
    return None

BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]

def decrypt_wallet(encrypted):
  password = BLOCKCHAIN_PASSWORD_1
  iterations = default_pbkdf2_iterations
  
  enc = base64.b64decode(encrypted)
  iv = enc[:AES.block_size]
  key = PBKDF2(password, iv, dkLen=32, count=iterations)  
  cipher = AES.new(key, AES.MODE_CBC, iv)
  content = unpad(cipher.decrypt(enc[AES.block_size:]))
  return json.loads(content)

def construct_data_tx(data, _from):
  # inputs
  coins_from = blockchain_info.coin_sources_for_address(_from)
  if len(coins_from) < 1:
    return "No free outputs to spend"
  max_coin_value, _, max_idx, max_h, max_script = max((tx_out.coin_value, random(), idx, h, tx_out.script) for h, idx, tx_out in coins_from)
  unsigned_txs_out = [UnsignedTxOut(max_h, max_idx, max_coin_value, max_script)]
  
  # outputs
  if max_coin_value > TX_FEES * 2:
    return 'max output greater than twice the threshold, too big.'
  if max_coin_value < TX_FEES:
    return 'max output smaller than threshold, too small.'
  script_text = 'OP_RETURN %s' % data.encode('hex')
  script_bin = tools.compile(script_text)
  new_txs_out = [TxOut(0, script_bin)]
  version = 1
  lock_time = 0
  unsigned_tx = UnsignedTx(version, unsigned_txs_out, new_txs_out, lock_time)
  return unsigned_tx


def tx2hex(tx):
  s = io.BytesIO()
  tx.stream(s)
  tx_bytes = s.getvalue()
  tx_hex = binascii.hexlify(tx_bytes).decode('utf8')
  return tx_hex


def publish_data_old(doc):
  recipient_list = [(addr, 1) for addr in doc.get_address_repr()]
  return sendmany(recipient_list, PAYMENT_ADDRESS)

def pushtxn(raw_tx):
  '''Insight send raw tx API'''
  url = 'https://insight.bitpay.com/api/tx/send'
  payload = urllib.urlencode({
    "rawtx": raw_tx 
  })
  result = urlfetch.fetch(url,
    method=urlfetch.POST,
    payload=payload
  )
  if result.status_code == 200:
    j = json.loads(result.content)
    txid = j.get('txid')
    return txid, raw_tx
  else:
    msg = 'Error accessing insight API:'+str(result.status_code)+" "+str(result.content)
    logging.error(msg)
    return None, msg
  
OP_RETURN_MAX_DATA = 40
POE_MARKER_BYTES = 'DOCPROOF'
def publish_data(data):

  data = POE_MARKER_BYTES + data
  if len(data) > OP_RETURN_MAX_DATA:
    return None, 'data too long for OP_RETURN: %s' % (data.encode('hex'))

  secret_exponent = wif_to_secret_exponent(PAYMENT_PRIVATE_KEY)
  _from = PAYMENT_ADDRESS
  
  unsigned_tx = construct_data_tx(data, _from)
  if type(unsigned_tx) == str: # error
    return (None, unsigned_tx)
  signed_tx = unsigned_tx.sign(SecretExponentSolver([secret_exponent]))
  raw_tx = tx2hex(signed_tx)
  txid, message = pushtxn(raw_tx)
  return txid, message
