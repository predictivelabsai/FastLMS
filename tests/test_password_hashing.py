"""Local users table passwords must use scrypt; legacy SHA256 upgrades on login."""

from __future__ import annotations

import hashlib
import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SESSION_SECRET", "fastlms-test-session-secret")

import main
from components.account_auth import AccountStore


def test_new_hashes_are_scrypt_not_sha256():
    encoded = main._hash_pw("correct-horse-battery")
    assert encoded.startswith("scrypt$16384$")
    assert "$" in encoded
    assert encoded != hashlib.sha256(b"correct-horse-battery").hexdigest()
    assert AccountStore._verify_password("correct-horse-battery", encoded)
    assert not AccountStore._verify_password("wrong", encoded)


def test_legacy_sha256_still_verifies():
    legacy = hashlib.sha256(b"admin").hexdigest()
    assert main._is_legacy_password_hash(legacy)
    assert main._verify_user_password("admin", legacy)
    assert not main._verify_user_password("nope", legacy)


def test_scrypt_and_legacy_round_trip():
    scrypt = main._hash_pw("admin")
    assert main._verify_user_password("admin", scrypt)
    assert not main._is_legacy_password_hash(scrypt)
