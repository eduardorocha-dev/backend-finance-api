"""Administrative commands.

    python -m app.cli make-admin user@example.com
    python -m app.cli revoke-admin user@example.com

`make admin email=...` wraps the first one.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

# Import every model so SQLAlchemy can resolve User's relationships.
import app.models.account  # noqa: F401
import app.models.budget  # noqa: F401
import app.models.category  # noqa: F401
import app.models.exchange_rate  # noqa: F401
import app.models.export  # noqa: F401
import app.models.recurring_transaction  # noqa: F401
import app.models.transaction  # noqa: F401
from app.models.user import User


def set_admin(session: Session, email: str, is_admin: bool) -> bool:
    """Set the admin flag on the user with this email. Returns False if there is no such user."""
    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        return False
    user.is_admin = is_admin
    session.commit()
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [
        ("make-admin", "give a user admin privileges"),
        ("revoke-admin", "remove a user's admin privileges"),
    ]:
        cmd = commands.add_parser(name, help=help_text)
        cmd.add_argument("email")
    args = parser.parse_args(argv)

    from app.db.sync_session import SyncSessionLocal

    with SyncSessionLocal() as session:
        if not set_admin(session, args.email, is_admin=args.command == "make-admin"):
            print(f"No user with email {args.email}", file=sys.stderr)
            return 1
    print(f"{args.email}: admin = {args.command == 'make-admin'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
