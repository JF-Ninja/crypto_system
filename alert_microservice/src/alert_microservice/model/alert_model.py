from alert_microservice.db import Base
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column


class Alert(Base):
    target_price: Mapped[float]
    is_triggered: Mapped[bool] = mapped_column(server_default=text("false"))
    user_id: Mapped[int]
    trigger_type:Mapped[str]
    ticker_name: Mapped[str]