"""
Blockchain.info Python Client for the JSON Merchant API for Google App Engine.
"""

from google.appengine.api import urlfetch
import logging
import json
import base64
from Crypto.Cipher import AES
from poster.encode import multipart_encode, MultipartParam

from pycoin import encoding
from pycoin.convention import satoshi_to_btc
from pycoin.services import blockchain_info
from pycoin.tx import UnsignedTx, SecretExponentSolver
from secrets import BLOCKCHAIN_WALLET_GUID, BLOCKCHAIN_PASSWORD_1, BLOCKCHAIN_PASSWORD_2, CALLBACK_SECRET
from Crypto.Protocol.KDF import PBKDF2
import io
import binascii

TX_FEES = 10000
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


BASE_BLOCKCHAIN_URL = "https://blockchain.info"

def get_base_blockchain_url(command):
    url = BASE_BLOCKCHAIN_URL
    url += "/merchant/%s/%s?password=%s" % (BLOCKCHAIN_WALLET_GUID, command, BLOCKCHAIN_PASSWORD_1)
    if len(BLOCKCHAIN_PASSWORD_2) > 0:
        url += "&second_password=%s" % (BLOCKCHAIN_PASSWORD_2)
    return url

def new_address():
    url = get_base_blockchain_url("new_address")
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        j = json.loads(result.content)
        return j["address"]
    else:
        logging.error('There was an error contacting the Blockchain.info API')
        return None

def address_balance(addr):
    url = BASE_BLOCKCHAIN_URL + "/address/%s?format=json&limit=0" % addr
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        return json.loads(result.content)["final_balance"]
    else:
        logging.error('There was an error contacting the Blockchain.info API')
        return None

def payment(to, satoshis, _from=None):
    url = get_base_blockchain_url("payment")
    url += "&to=%s&amount=%s&shared=%s&fee=%s" % (to, int(satoshis), "false", TX_FEES)
    if _from:
        url += "&from=%s" % (_from)
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        return json.loads(result.content).get("tx_hash")
    else:
        logging.error('There was an error contacting the Blockchain.info API')
        return None

def sendmany(recipient_list, _from=None):
    url = get_base_blockchain_url("sendmany")
    # can't do it using python dict because we have repeated addresses
    recipients = "{"
    for addr, satoshis in recipient_list:
        recipients += '"%s":%s,' % (addr, satoshis)
    recipients = recipients[:-1]
    recipients += "}"
    url += "&recipients=%s&shared=%s&fee=%s" % (recipients, "false", TX_FEES)
    if _from:
        url += "&from=%s" % (_from)
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        return json.loads(result.content).get("tx_hash")
    else:
        logging.error('There was an error contacting the Blockchain.info API')
        return None

def get_tx(tx_hash):
    url = BASE_BLOCKCHAIN_URL + "/rawtx/%s" % (tx_hash)
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        return json.loads(result.content)
    else:
        logging.error('There was an error contacting the Blockchain.info API')
        return None
def get_block(height):
    if not height:
        return None
    url = BASE_BLOCKCHAIN_URL + "/block-height/%s?format=json" % (height)
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        return json.loads(result.content).get("blocks")[0]
    else:
        logging.error('There was an error contacting the Blockchain.info API')
        return None

def callback_secret_valid(secret):
    return secret == CALLBACK_SECRET

def get_encrypted_wallet():
    url = BASE_BLOCKCHAIN_URL + "/wallet/%s?format=%s" % (BLOCKCHAIN_WALLET_GUID, "json")
    logging.warn(url)
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        j = json.loads(result.content)
        return j.get("payload")
    else:
        logging.error("Blockchain Error getting wallet from url %s, got result \n%d %s" % (url, result.status_code, result.content))
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

def push_tx(raw_tx):
    url = "https://blockchain.info/pushtx"
    
    params = []
 
    params.append(MultipartParam(
        "tx",
        filetype='text/plain',
        value=raw_tx))
        
    payloadgen, headers = multipart_encode(params)
            
    payload = str().join(payloadgen)
          
    result = urlfetch.fetch(
        url=url,
        payload=payload,
        method=urlfetch.POST,
        headers=headers)
    
    if result.status_code == 200:
        return result.content
    else:
        logging.error("Blockchain Error pushing raw tx %s got result \n%d %s" % (raw_tx, result.status_code, result.content))
        return None

def manual_send(_from, recipient_list, fee=TX_FEES):
    
    encrypted = get_encrypted_wallet()
    decrypted = decrypt_wallet(encrypted)
    
    secret_exponent = None
    for key_data in decrypted["keys"]:
        pk = key_data["priv"]
        addr = key_data["addr"]
        if _from == addr:
            secret_exponent = encoding.from_bytes_32(encoding.a2b_base58(pk))
    
    if not secret_exponent:
        return "couldn't find private key for address %s" % _from 
    
    total_value = 0
    coins_from = []
    coins_sources = blockchain_info.coin_sources_for_address(_from)
    coins_from.extend(coins_sources)
    total_value += sum(cs[-1].coin_value for cs in coins_sources)
  
    coins_to = []
    total_spent = 0
    for addr, satoshis in recipient_list:
        total_spent += satoshis
        coins_to.append((satoshis, addr))
    change = (total_value - total_spent) - fee
    if change > 0:
        coins_to.append((change, _from))
    if change < 0:
        return "don't have funds for transaction fees."
    actual_tx_fee = total_value - total_spent
    if actual_tx_fee < fee:
        return "not enough source coins (%s BTC) for destination (%s BTC). Short %s BTC" % (satoshi_to_btc(total_value), satoshi_to_btc(total_spent), satoshi_to_btc(-actual_tx_fee))
    if actual_tx_fee > fee:
        return "transacion fee too high, aborting: %s BTC" % (satoshi_to_btc(actual_tx_fee))
    
    unsigned_tx = UnsignedTx.standard_tx(coins_from, coins_to)
    solver = SecretExponentSolver([secret_exponent])
    new_tx = unsigned_tx.sign(solver)
    s = io.BytesIO()
    new_tx.stream(s)
    tx_bytes = s.getvalue()
    tx_hex = binascii.hexlify(tx_bytes).decode("utf8")
    return push_tx(tx_hex)
