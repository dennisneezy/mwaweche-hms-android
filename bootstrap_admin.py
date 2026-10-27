"""Create the first API administrator interactively. Run once on the mother server."""
import getpass, os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from app import Base, User, DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(engine)
username = input("New administrator username: ").strip()
if not username: raise SystemExit("Username is required")
password = getpass.getpass("New administrator password (minimum 14 characters): ")
confirm = getpass.getpass("Confirm password: ")
if len(password) < 14 or password != confirm: raise SystemExit("Passwords must match and be at least 14 characters")
with Session(engine) as db:
    if db.scalar(select(User).where(User.username == username)): raise SystemExit("That username already exists")
    db.add(User(username=username, password_hash=PasswordHash.recommended().hash(password), role="Administrator", active=True)); db.commit()
print("Administrator created. Store credentials securely.")
