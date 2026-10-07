import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet
from django.conf import settings


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token():
    return secrets.token_urlsafe(32)


def _fernet():
    source = settings.KAZILAYER_MFA_ENCRYPTION_KEY or settings.SECRET_KEY
    key = base64.urlsafe_b64encode(hashlib.sha256(source.encode()).digest())
    return Fernet(key)


def encrypt_secret(secret):
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(value):
    return _fernet().decrypt(value.encode()).decode()


def generate_totp_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp_code(secret, timestamp=None):
    timestamp = int(timestamp or time.time())
    counter = timestamp // 30
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    digest = hmac.new(
        base64.b32decode(padded), struct.pack(">Q", counter), hashlib.sha1
    ).digest()
    offset = digest[-1] & 0x0F
    value = (
        struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    ) % 1_000_000
    return f"{value:06d}"


def verify_totp(secret, code):
    return any(
        hmac.compare_digest(
            totp_code(secret, time.time() + offset * 30), str(code).zfill(6)
        )
        for offset in (-1, 0, 1)
    )


def provisioning_uri(secret, email):
    issuer = "KaziLayer"
    return f"otpauth://totp/{quote(issuer)}:{quote(email)}?secret={secret}&issuer={quote(issuer)}&digits=6&period=30"
