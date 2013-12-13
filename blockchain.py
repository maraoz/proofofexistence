"""
Blockchain.info Python Client for the JSON Merchant API for Google App Engine.
"""

from google.appengine.api import urlfetch
import logging
import json
import base64
from Crypto.Cipher import AES
from poster.encode import multipart_encode, MultipartParam
from pycoin.tx.script import tools
from pycoin.convention import satoshi_to_btc
from pycoin.services import blockchain_info
from pycoin.encoding import wif_to_secret_exponent,\
    bitcoin_address_to_hash160_sec
from pycoin.tx import UnsignedTx, SecretExponentSolver, TxOut
from secrets import BLOCKCHAIN_WALLET_GUID, BLOCKCHAIN_PASSWORD_1, BLOCKCHAIN_PASSWORD_2, CALLBACK_SECRET,\
    BLOCKCHAIN_ENCRYPTED_WALLET, PAYMENT_PRIVATE_KEY, PAYMENT_ADDRESS
from Crypto.Protocol.KDF import PBKDF2
import io
import binascii
from pycoin.tx.Tx import Tx
from pycoin.tx.TxIn import TxIn
from pycoin.tx.UnsignedTx import UnsignedTxOut
from pycoin.serialize import b2h

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

def get_txs_for_addr(self, addr, limit=5):
    url = BASE_BLOCKCHAIN_URL + "/address/%s?format=json&limit=%s" % (addr, limit)
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        j = json.loads(result.content)
        return [(tx["hash"], tx["time"]) for tx in j["txs"]]
    else:
        logging.error("Error accessing blockchain API: " + str(result.status_code))
        return None

def has_txs(self, addr):
    return len(get_txs_for_addr(addr, 1)) > 0


def callback_secret_valid(secret):
    return secret == CALLBACK_SECRET

def get_encrypted_wallet(offline=True):
    if offline:
        return BLOCKCHAIN_ENCRYPTED_WALLET
    url = BASE_BLOCKCHAIN_URL + "/wallet/%s?format=%s" % (BLOCKCHAIN_WALLET_GUID, "json")
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        j = json.loads(result.content)
        return j
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

def construct_data_tx(data, _from):
    
    # inputs
    coins_from = blockchain_info.coin_sources_for_address(_from)
    unsigned_txs_out = [UnsignedTxOut(h, idx, tx_out.coin_value, tx_out.script) for h, idx, tx_out in coins_from]
    total_value = sum(cs[-1].coin_value for cs in coins_from)
    
    # outputs
    change = total_value - TX_FEES
    if change < 0:
        return "don't have funds for transaction fees."
    script_text = "OP_RETURN %s" % data.encode("hex")
    script_bin = tools.compile(script_text)
    STANDARD_SCRIPT_OUT = "OP_DUP OP_HASH160 %s OP_EQUALVERIFY OP_CHECKSIG"
    new_txs_out = [TxOut(0, script_bin)]
    for coin_value, bitcoin_address in [(change, _from)]:
        hash160 = bitcoin_address_to_hash160_sec(bitcoin_address, False)
        script_text = STANDARD_SCRIPT_OUT % b2h(hash160)
        script_bin = tools.compile(script_text)
        new_txs_out.append(TxOut(coin_value, script_bin))
    
    version = 1
    lock_time = 0
    unsigned_tx = UnsignedTx(version, unsigned_txs_out, new_txs_out, lock_time)
    return unsigned_tx

def publish_data(data):
    
    secret_exponent = wif_to_secret_exponent(PAYMENT_PRIVATE_KEY)
    _from = PAYMENT_ADDRESS
    
    unsigned_tx = construct_data_tx(data, _from)
    solver = SecretExponentSolver([secret_exponent])
    new_tx = unsigned_tx.sign(solver)
    s = io.BytesIO()
    new_tx.stream(s)
    tx_bytes = s.getvalue()
    tx_hex = binascii.hexlify(tx_bytes).decode("utf8")
    return (tx_hex)
