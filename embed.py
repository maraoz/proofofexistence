import hashlib
from b58 import encode as base58_encode, decode as base58_decode

def hide_in_address(x):
    assert isinstance(x, bytes)
    assert len(x) == 20
 
    return '1' + base58_check(x)

def base58_check(src):
    src = bytes("\0") + src
    hasher = hashlib.sha256()
    hasher.update(src)
    r = hasher.digest()
 
    hasher = hashlib.sha256()
    hasher.update(r)
    r = hasher.digest()
 
    checksum = r[:4]
    s = src + checksum
 
    return base58_encode(int(s.encode('hex'), 16))

def recover_message(addr):
    n = base58_decode(addr)
    return '{0:030X}'.format(n)[:-8].decode("hex")
 
if __name__ == '__main__':
    
    secret = "mytwentycharactertxt"
    
    message = bytes(secret)
    
    addr = hide_in_address(message)
    print addr
    m = recover_message(addr)
    print m
