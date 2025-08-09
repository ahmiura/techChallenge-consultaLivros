from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from ..db.database import Base

class LogRequest(Base):
    __tablename__ = "log_requests"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    method = Column(String)
    path = Column(String)
    status_code = Column(Integer)
    process_time_ms = Column(Float)