import bcrypt
import passlib
from passlib.context import CryptContext

# Applying the monkeypatch
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (object,), {"__version__": getattr(bcrypt, "__version__", "5.0.0")})

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test():
    password = "admin123"
    print(f"Testing password: {password}")
    try:
        hashed = pwd_context.hash(password)
        print(f"Hashed: {hashed}")
        verified = pwd_context.verify(password, hashed)
        print(f"Verified: {verified}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
