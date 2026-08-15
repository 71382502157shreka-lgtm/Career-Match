import pytest
from app.core.security import hash_password, get_password_hash, verify_password, create_access_token, decode_access_token


def test_password_hashing_and_verification():
    password = "SecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_password_hash_alias():
    password = "AnotherPassword456!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True


def test_jwt_create_and_decode():
    subject = "user@example.com"
    token = create_access_token(subject=subject)
    assert token is not None
    decoded_sub = decode_access_token(token)
    assert decoded_sub == subject


def test_decode_invalid_token():
    assert decode_access_token("invalid.jwt.token") is None
    assert decode_access_token("") is None
