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


def reset_db_command(args: argparse.Namespace) -> int:
    """Safely resets the database by clearing data or dropping/recreating tables."""
    from project_management_api.db.session import engine, Base
    import project_management_api.models  # Ensure all models are loaded
    from sqlalchemy.sql import text

    dialect_name = engine.dialect.name
    print(f"Target Database Engine: {dialect_name.upper()} ({engine.url.render_as_string(hide_password=True)})")

    if not args.force:
        try:
            confirm = input(
                f"WARNING: This will delete ALL data in the '{engine.url.database}' database!\n"
                "Are you absolutely sure you want to continue? (type 'yes' to proceed): "
            ).strip()
            if confirm != "yes":
                print("Aborted.")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return 1

    tables = [
        "comment_attachments",
        "task_comments",
        "task_activities",
        "tasks",
        "project_members",
        "projects",
        "workspace_access_requests",
        "workspace_members",
        "workspaces",
        "company_invitations",
        "company_members",
        "company_creation_requests",
        "companies",
        "user_otps",
        "audit_logs",
        "users",
    ]

    with engine.connect() as conn:
        with conn.begin():
            if args.drop_all:
                print("Dropping and recreating all tables...")
                Base.metadata.drop_all(bind=conn)
                Base.metadata.create_all(bind=conn)
                print("All tables dropped and recreated successfully.")
            else:
                print("Truncating tables while preserving schema...")
                if dialect_name == "mysql":
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                    for tbl in tables:
                        check = conn.execute(
                            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = :t"),
                            {"t": tbl},
                        ).scalar()
                        if check:
                            conn.execute(text(f"TRUNCATE TABLE `{tbl}`;"))
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                elif dialect_name in ["postgresql", "postgres"]:
                    existing = []
                    for tbl in tables:
                        check = conn.execute(
                            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :t)"),
                            {"t": tbl},
                        ).scalar()
                        if check:
                            existing.append(f'"{tbl}"')
                    if existing:
                        conn.execute(text(f"TRUNCATE TABLE {', '.join(existing)} CASCADE;"))
                else:
                    for tbl in tables:
                        conn.execute(text(f"DELETE FROM {tbl};"))

                print("All application table data cleared successfully while preserving schema and migration history.")

    return 0


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

    reset_cmd = subparsers.add_parser(
        "reset-db",
        help="Clear all database table data or drop and recreate tables",
    )
    reset_cmd.add_argument(
        "--keep-schema",
        action="store_true",
        default=True,
        help="Clear table data while preserving the table structure (default)",
    )
    reset_cmd.add_argument(
        "--drop-all",
        action="store_true",
        help="Drop and recreate all tables instead of truncating data",
    )
    reset_cmd.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip interactive confirmation prompt",
    )
    reset_cmd.set_defaults(func=reset_db_command)

    args = parser.parse_args()
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
