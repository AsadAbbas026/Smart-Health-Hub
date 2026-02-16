import hashlib

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.
    Returns the hexadecimal hash string.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain password against the hashed password.
    Returns True if they match, False otherwise.
    """
    return hash_password(password) == password_hash
