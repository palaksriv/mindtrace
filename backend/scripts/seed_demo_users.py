"""Create idempotent local demo accounts for the Day 2 MVP."""

from sqlalchemy import select

from app.auth.passwords import hash_password
from app.database import SessionLocal, create_database_tables
from app.models.user import User, UserRole

DEMO_USERS = (
    ("Demo Student", "student@example.com", "StudentDemo2026!", UserRole.STUDENT),
    ("Demo Counsellor", "counsellor@example.com", "CounsellorDemo2026!", UserRole.COUNSELLOR),
)


def main() -> None:
    create_database_tables()
    with SessionLocal() as database:
        for name, email, password, role in DEMO_USERS:
            if database.scalar(select(User).where(User.email == email)) is None:
                database.add(
                    User(name=name, email=email, password_hash=hash_password(password), role=role)
                )
                print(f"Created {role.value} demo account: {email}")
        database.commit()


if __name__ == "__main__":
    main()
