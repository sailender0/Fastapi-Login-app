import pyotp

# This secret should ideally be stored in your DB per user, 
# but for a quick start, we can generate a temporary one.
def generate_mfa_code():
    # Generates a random base32 secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, interval=300) # Valid for 5 minutes
    return totp.now(), secret

def verify_mfa_code(secret: str, code: str):
    totp = pyotp.TOTP(secret, interval=300)
    return totp.verify(code)