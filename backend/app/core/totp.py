import pyotp


def new_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, *, username: str, issuer: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def verify_code(secret: str, code: str) -> bool:
    if not code or not code.strip().isdigit() or len(code.strip()) != 6:
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)
