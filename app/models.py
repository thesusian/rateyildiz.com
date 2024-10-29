from sqlalchemy import Boolean, Column, Integer, String, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)
    gmail = Column(String(255), unique=True, index=True)
    admin = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    student_email= Column(String(255), unique=True, nullable=True)
    google_id = Column(String(255), unique=True, index=True)
    picture = Column(String(1024), nullable=True)
    locale = Column(String(50), nullable=True)
    verification_code = Column(String(64), nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    verification_attempts = Column(Integer, default=0)
    last_verification_attempt = Column(DateTime, nullable=True)

class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)
    image_id = Column(String(255), nullable=True)
    username = Column(String(255), unique=True, index=True)
    avesis_id = Column(Integer, unique=True)
    faculty_id = Column(Integer)
    departments = Column(String(1023))

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    professor_id = Column(Integer, ForeignKey("professors.id"))
    comment = Column(String(1000))
    english_proficiency = Column(Integer)
    friendliness = Column(Integer)
    knowledge = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")
    professor = relationship("Professor", back_populates="ratings")

    __table_args__ = (
        CheckConstraint('english_proficiency >= 5 AND english_proficiency <= 50 AND english_proficiency % 5 = 0'),
        CheckConstraint('friendliness >= 5 AND friendliness <= 50 AND friendliness % 5 = 0'),
        CheckConstraint('knowledge >= 5 AND knowledge <= 50 AND knowledge % 5 = 0'),
    )

User.ratings = relationship("Rating", back_populates="user")
Professor.ratings = relationship("Rating", back_populates="professor")
