import argparse
import getpass
import re
import sys
from sqlalchemy.orm import Session

from project_management_api.core.security import hash_password
from project_management_api.crud.audit import create_audit_log
from project_management_api.crud.user import get_user_by_email
from project_management_api.db.session import SessionLocal
from project_management_api.models.user import User


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def create_superuser_command(args: argparse.Namespace, db: Session | None = None) -> int:
    """Creates a new superuser or promotes an existing user to superuser."""
    email = args.email
    if not email:
        try:
            email = input("Enter superuser email: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return 1

    if not email or not validate_email(email):
        print("Error: Invalid email format.", file=sys.stderr)
        return 1

    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    try:
        existing_user = get_user_by_email(db, email=email)

        if existing_user:
            if not args.promote:
                print(
                    f"User with email '{email}' already exists. Use '--promote' flag if you want to promote this user to superuser.",
                    file=sys.stderr,
                )
                return 1

            if existing_user.is_superuser:
                print(f"User '{email}' is already a superuser.")
                return 0

            # Promote existing user
            existing_user.is_superuser = True
            existing_user.is_active = True
            existing_user.is_verified = True

            create_audit_log(
                db,
                action="SUPERUSER_PROMOTED_CLI",
                resource_type="USER",
                resource_id=existing_user.id,
                actor_id=existing_user.id,
                details={"email": existing_user.email, "method": "CLI"},
            )
            db.commit()
            print(f"Successfully promoted existing user '{email}' to SUPERUSER.")
            return 0

        # Create new superuser
        full_name = args.full_name
        if not full_name:
            try:
                full_name = input("Enter superuser full name: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return 1

        if not full_name or len(full_name) < 2:
            print("Error: Full name must be at least 2 characters.", file=sys.stderr)
            return 1

        password = args.password
        if not password:
            try:
                password = getpass.getpass("Enter superuser password (min 8 chars): ")
                confirm_password = getpass.getpass("Confirm password: ")
                if password != confirm_password:
                    print("Error: Passwords do not match.", file=sys.stderr)
                    return 1
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return 1

        if not password or len(password) < 8:
            print("Error: Password must be at least 8 characters.", file=sys.stderr)
            return 1

        new_superuser = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )
        db.add(new_superuser)
        db.commit()
        db.refresh(new_superuser)

        create_audit_log(
            db,
            action="SUPERUSER_CREATED_CLI",
            resource_type="USER",
            resource_id=new_superuser.id,
            actor_id=new_superuser.id,
            details={"email": new_superuser.email, "method": "CLI"},
        )
        db.commit()

        print(f"Superuser '{email}' successfully created and activated.")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Error creating superuser: {e}", file=sys.stderr)
        return 1
    finally:
        if should_close_db:
            db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="project-management-api",
        description="Project Management API Administration CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_su = subparsers.add_parser(
        "create-superuser",
        help="Create a new superuser or promote an existing user to superuser",
    )
    create_su.add_argument("--email", "-e", type=str, help="Email address for the superuser")
    create_su.add_argument("--password", "-p", type=str, help="Password (min 8 chars)")
    create_su.add_argument("--full-name", "-n", type=str, help="Full name for the new superuser")
    create_su.add_argument(
        "--promote",
        action="store_true",
        help="Promote user to superuser if the email already exists",
    )
    create_su.set_defaults(func=create_superuser_command)

    args = parser.parse_args()
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
