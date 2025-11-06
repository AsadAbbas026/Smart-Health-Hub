# database/queries/users_queries.py
from database.connection import SessionLocal, get_connection
from database.models.User import User, UserRole

def insert_user_local(uid, email, password, name, role):
    session = SessionLocal()
    try:
        user = User(
            user_id=uid,
            email=email,
            password_hash=password,
            name=name,
            role=UserRole(role)
        )
        session.add(user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error inserting user locally: {e}")
        return False
    finally:
        session.close()

def get_user_by_email(email: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        return user
    except Exception as e:
        print(f"❌ Error fetching user by email: {e}")
        return None
    finally:
        session.close()
