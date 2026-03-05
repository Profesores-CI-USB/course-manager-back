import argparse
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import User


async def create_admin(email: str, password: str, full_name: str | None) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        user = existing.scalar_one_or_none()

        if user is not None:
            if user.role == "admin":
                print(f"El usuario {email} ya es admin")
                return

            user.role = "admin"
            if full_name is not None:
                user.full_name = full_name
            user.hashed_password = hash_password(password)

            db.add(user)
            await db.commit()
            print(f"Usuario existente promovido a admin: {email}")
            return

        new_admin = User(
            email=email,
            full_name=full_name,
            role="admin",
            hashed_password=hash_password(password),
        )
        db.add(new_admin)
        await db.commit()
        print(f"Admin creado correctamente: {email}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crear (o promover) un usuario admin")
    parser.add_argument("--email", required=True, help="Correo del admin")
    parser.add_argument("--password", required=True, help="Contraseña del admin")
    parser.add_argument("--full-name", default=None, help="Nombre completo (opcional)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(create_admin(args.email, args.password, args.full_name))


if __name__ == "__main__":
    main()
