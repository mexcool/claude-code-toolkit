#!/usr/bin/python3
import sys, requests, json, re, base64, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

#
# Script to upload/download to/from pastila.nl from command line.
# Put it somewhere in PATH and use like this:
#
# % echo henlo | pastila.py
# https://pastila.nl/?cafebabe/c8570701492af2ac7269064a661686e3#oj6jpBCRzIOSGTgRFgMquA==
#
# % pastila.py 'https://pastila.nl/?cafebabe/c8570701492af2ac7269064a661686e3#oj6jpBCRzIOSGTgRFgMquA=='
# henlo
#


def sipHash128(m: bytes):
    mask = (1 << 64) - 1

    def rotl(v, offset, bits):
        v[offset] = ((v[offset] << bits) & mask) | ((v[offset] & mask) >> (64 - bits))

    def compress(v):
        v[0] += v[1]
        v[2] += v[3]
        rotl(v, 1, 13)
        rotl(v, 3, 16)
        v[1] ^= v[0]
        v[3] ^= v[2]
        rotl(v, 0, 32)
        v[2] += v[1]
        v[0] += v[3]
        rotl(v, 1, 17)
        rotl(v, 3, 21)
        v[1] ^= v[2]
        v[3] ^= v[0]
        rotl(v, 2, 32)

    v = [0x736f6d6570736575, 0x646f72616e646f6d, 0x6c7967656e657261, 0x7465646279746573]
    offset = 0
    while offset < len(m) - 7:
        word = int.from_bytes(m[offset:offset + 8], 'little')
        v[3] ^= word
        compress(v)
        compress(v)
        v[0] ^= word
        offset += 8

    buf = bytearray(8)
    buf[:len(m) - offset] = m[offset:]
    buf[7] = len(m) & 0xff

    word = int.from_bytes(buf, 'little')
    v[3] ^= word
    compress(v)
    compress(v)
    v[0] ^= word
    v[2] ^= 0xFF
    compress(v)
    compress(v)
    compress(v)
    compress(v)

    hash_val = ((v[0] ^ v[1]) & mask) + (((v[2] ^ v[3]) & mask) << 64)
    s = '{:032x}'.format(hash_val)
    return ''.join(s[i:i+2] for i in range(30,-2,-2))

def error(s):
    sys.stderr.write(f"error: {s}\n")
    sys.exit(1)

def getFingerprint(text):
    """Generate fingerprint from text content (matches JS implementation)"""
    # Match unicode letter sequences of 4-100 characters
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    matches = re.findall(r'[^\W\d_]{4,100}', text, re.UNICODE)
    if not matches:
        return 'ffffffff'
    # Create triplets of consecutive words
    triplets = [','.join(matches[i:i+3]) for i in range(len(matches) - 2)]
    # Get unique triplets
    unique_triplets = list(set(triplets))
    # Hash each triplet and take first 8 chars
    hashes = [sipHash128(t.encode('utf-8'))[:8] for t in unique_triplets]
    hashes.append('ffffffff')
    return min(hashes)

def load(url):
    r = re.match(r"^(?:(?:(?:(?:(?:https?:)?//)?pastila\.nl)?/)?\?)?([a-f0-9]+)/([a-f0-9]+)(?:#(.+))?$", url)
    if r is None: error('bad url')
    fingerprint, hash_hex, key = r.groups()

    # Public pastila.nl backend — see https://github.com/ClickHouse/pastila
    response = requests.post('https://uzg8q0g12h.eu-central-1.aws.clickhouse.cloud/?user=paste', data=f"SELECT content, is_encrypted FROM data_view(fingerprint = '{fingerprint}', hash = '{hash_hex}') FORMAT JSON")
    if not response.ok: error(f"{response} {response.content}")

    j = json.loads(response.content)
    if j['rows'] != 1: error("paste not found")
    #if 'statistics' in j: sys.stderr.write(f"{j['statistics']}")
    content, is_encrypted = j['data'][0]['content'], j['data'][0]['is_encrypted']

    if is_encrypted:
        if key is None: error("paste is encrypted, but the url contains no key (part after '#')")

        # Check for GCM mode (web interface) vs CTR mode (CLI)
        if key.endswith('GCM'):
            # AES-GCM mode (used by web interface)
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            key = base64.b64decode(key[:-3])  # strip 'GCM' suffix
            content = base64.b64decode(content)
            # First 12 bytes of key are the IV/nonce
            iv = key[:12]
            aes_key = key
            aesgcm = AESGCM(aes_key)
            decrypted = aesgcm.decrypt(iv, content, None)
            content = decrypted
        else:
            # AES-CTR mode (used by CLI)
            key = base64.b64decode(key)
            content = base64.b64decode(content)
            cipher = Cipher(algorithms.AES(key), modes.CTR(b'\x00' * 16), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(content) + decryptor.finalize()
            content = decrypted

    return content

def save(data, encrypt):
    # Compute fingerprint on original data before encryption
    fingerprint = getFingerprint(data)

    key = os.urandom(16)
    url_suffix = ""
    if encrypt:
        # Use AES-GCM (same as web interface)
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        iv = key[:12]  # First 12 bytes of key as IV
        aesgcm = AESGCM(key)
        encrypted = aesgcm.encrypt(iv, data, None)
        data = base64.b64encode(encrypted)
        url_suffix = '#' + base64.b64encode(key).decode() + 'GCM'

    h = sipHash128(data)

    payload = json.dumps({
        'fingerprint_hex': fingerprint,
        'hash_hex': h,
        'content': data.decode(),
        'is_encrypted': encrypt,
    })
    # Public pastila.nl backend — see https://github.com/ClickHouse/pastila
    response = requests.post('https://uzg8q0g12h.eu-central-1.aws.clickhouse.cloud/?user=paste', data=f'INSERT INTO data (fingerprint_hex, hash_hex, content, is_encrypted) FORMAT JSONEachRow {payload}')
    if not response.ok: error(f"{response} {response.content}")
    print(f"https://pastila.nl/?{fingerprint}/{h}{url_suffix}")


def is_url(s):
    """Check if string looks like a pastila URL"""
    return bool(re.match(r"^(?:https?://)?pastila\.nl", s) or re.match(r"^\?[a-f0-9]+/[a-f0-9]+", s))

if len(sys.argv) == 1:
    # No args: read from stdin
    data = sys.stdin.buffer.read()
    save(data, True)
elif len(sys.argv) == 2:
    arg = sys.argv[1]
    if is_url(arg):
        # It's a pastila URL: decrypt and output
        data = load(arg)
        sys.stdout.buffer.write(data)
    elif os.path.isfile(arg):
        # It's a file path: read and upload
        with open(arg, 'rb') as f:
            data = f.read()
        save(data, True)
    else:
        # Treat as direct text to upload
        data = arg.encode('utf-8')
        save(data, True)
else:
    # Multiple args: join as text and upload
    data = ' '.join(sys.argv[1:]).encode('utf-8')
    save(data, True)
