from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from user_microservice.db import Base, uniq_str


class User(Base):
    email: Mapped[uniq_str]
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("false"))