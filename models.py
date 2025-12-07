from sqlalchemy import Column, Integer, String, Text
from database import Base

class Interest(Base):
    __tablename__ = "interest"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    role = Column(String)
    property = Column(String)
    message = Column(Text)
    funding = Column(String)
