import re

def validate_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def validate_password(password):
    return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)

def validate_phone_number(phone):
    # Allows digits, optional leading '+', and 10–15 digits typical for international formats
    return bool(re.match(r"^\+?\d{10,15}$", phone))