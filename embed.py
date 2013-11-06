"""Data Embedding algorithms for bitcoin addresses""" 

import hashlib
from b58 import encode as base58_encode, decode as base58_decode

TESTNET = False
version = 0 if not TESTNET else 111

def hide_in_address(x):
    assert isinstance(x, bytes)
    assert len(x) == 20
 
    return base58_check_encode(x, version)

def recover_message(addr):
    data = base58_check_decode(addr, version)
    return data

def dhash(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()

def rhash(s):
    h1 = hashlib.new('ripemd160')
    h1.update(hashlib.sha256(s).digest())
    return h1.digest()


def base58_encode_padded(s):
    res = base58_encode(int('0x' + s.encode('hex'), 16))
    pad = 0
    for c in s:
        if c == chr(0):
            pad += 1
        else:
            break
    return '1' * pad + res

def base58_decode_padded(s):
    pad = 0
    for c in s:
        if c == '1':
            pad += 1
        else:
            break
    h = '%x' % base58_decode(s)
    if len(h) % 2:
        h = '0' + h
    res = h.decode('hex')
    return chr(0) * pad + res

def base58_check_encode(s, version=0):
    vs = chr(version) + s
    check = dhash(vs)[:4]
    return base58_encode_padded(vs + check)

def base58_check_decode(s, version=0):
    k = base58_decode_padded(s)
    v0, data, check0 = k[0], k[1:-4], k[-4:]
    check1 = dhash(v0 + data)[:4]
    if check0 != check1:
        raise BaseException('checksum error')
    if version != ord(v0):
        raise BaseException('version mismatch')
    return data

if __name__ == '__main__':
    
    secret = "mytwentycharactertxt"
    message = bytes(secret)
    
    print "Original data:\t\t\t", message
    addr = hide_in_address(message)
    print "Address containing data:\t", addr
    m = recover_message(addr)
    print "Recovered data:\t\t\t", m
