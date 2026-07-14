from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    filename = Column(
        String(255),
        nullable=False
    )

    object_name = Column(
        String(500),
        nullable=False
    )

    content_type = Column(
        String(100)
    )

    size = Column(
        BigInteger
    )

    status = Column(
        String(50),
        nullable=False,
        default="uploaded"
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )