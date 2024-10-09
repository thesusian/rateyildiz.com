from sqlalchemy import Boolean, Column, Integer, String, DateTime, func, desc
from sqlalchemy.orm import Session, joinedload, aliased
from . import models
from datetime import datetime, timedelta
import random
import string
import time

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds to execute.")
        return result
    return wrapper

# User ops

def get_user_by_student_email(db: Session, student_email: str):
    return db.query(models.User).filter(models.User.student_email == student_email).first()

def set_verification_code_email(db: Session, user: models.User, student_email: str):
    code = ''.join(random.choices(string.digits, k=6))
    user.student_email = student_email  # type: ignore
    user.verification_code = code  # type: ignore
    user.verification_code_expires = datetime.utcnow() + timedelta(hours=24)  # type: ignore
    db.commit()
    db.refresh(user)
    return code

def verify_user(db: Session, user: models.User, student_email: str):
    user.verified = True  # type: ignore
    user.student_email = student_email  # type: ignore
    user.verification_code = None  # type: ignore
    user.verification_code_expires = None # type: ignore
    db.commit()
    db.refresh(user)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.gmail == email).first()

def get_user_by_google_id(db: Session, google_id: str):
    return db.query(models.User).filter(models.User.google_id == google_id).first()

def create_user(db: Session, user_data: dict):
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: models.User, user_data: dict):
    for key, value in user_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


# Professor ops

def create_professor(db: Session, full_name: str, image_url: str):
    db_professor = models.Professor(full_name=full_name, image_url=image_url)
    db.add(db_professor)
    db.commit()
    db.refresh(db_professor)
    return db_professor

def get_professor(db: Session, professor_id: int):
    return db.query(models.Professor).filter(models.Professor.id == professor_id).first()

def get_all_professors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Professor).order_by(func.random()).limit(100).all()

def search_professors(db: Session, query: str):
    return db.query(models.Professor).filter(models.Professor.full_name.ilike(f"%{query}%")).all()

def update_professor(db: Session, professor_id: int, full_name: str, image_url: str):
    db_professor = get_professor(db, professor_id)
    if db_professor:
        db_professor.full_name = full_name # type: ignore
        db_professor.image_url = image_url # type: ignore
        db.commit()
        db.refresh(db_professor)
    return db_professor

def delete_professor(db: Session, professor_id: int):
    db_professor = get_professor(db, professor_id)
    if db_professor:
        db.delete(db_professor)
        db.commit()
    return db_professor


# Rating ops

def create_rating(db: Session, user_id: int, professor_id: int, comment: str, english_proficiency: int, friendliness: int, knowledge: int):
    db_rating = models.Rating(
        user_id=user_id,
        professor_id=professor_id,
        comment=comment,
        english_proficiency=english_proficiency,
        friendliness=friendliness,
        knowledge=knowledge
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

def get_professor_ratings(db: Session, professor_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Rating).options(joinedload(models.Rating.user)).filter(models.Rating.professor_id == professor_id).offset(skip).limit(limit).all()

def get_professor_average_ratings(db: Session, professor_id: int):
    return db.query(
        func.avg(models.Rating.english_proficiency).label("avg_english"),
        func.avg(models.Rating.friendliness).label("avg_friendliness"),
        func.avg(models.Rating.knowledge).label("avg_knowledge")
    ).filter(models.Rating.professor_id == professor_id).first()

def get_user_rating_for_professor(db: Session, user_id: int, professor_id: int):
    return db.query(models.Rating).filter(
        models.Rating.user_id == user_id,
        models.Rating.professor_id == professor_id
    ).first()

def get_rating(db: Session, rating_id: int):
    return db.query(models.Rating).filter(models.Rating.id == rating_id).first()

def update_rating(db: Session, rating_id: int, comment: str, english_proficiency: int, friendliness: int, knowledge: int):
    db_rating = db.query(models.Rating).filter(models.Rating.id == rating_id).first()
    if db_rating:
        db_rating.comment = comment
        db_rating.english_proficiency = english_proficiency
        db_rating.friendliness = friendliness
        db_rating.knowledge = knowledge
        db.commit()
        db.refresh(db_rating)
    return db_rating

def delete_rating(db: Session, rating_id: int):
    db_rating = get_rating(db, rating_id)
    if db_rating:
        db.delete(db_rating)
        db.commit()
    return db_rating

@timer_decorator
def get_leaderboard_data(db: Session):
    return db.query(
        models.Professor.id,
        models.Professor.full_name,
        models.Professor.image_id,
        func.avg(models.Rating.english_proficiency).label('avg_english'),
        func.avg(models.Rating.friendliness).label('avg_friendliness'),
        func.avg(models.Rating.knowledge).label('avg_knowledge'),
        ((func.avg(models.Rating.english_proficiency) + func.avg(models.Rating.friendliness) + func.avg(models.Rating.knowledge)) / 3.0).label('avg_total')
    ).join(models.Rating).group_by(models.Professor.id).order_by(desc('avg_total')).limit(100).all()

@timer_decorator
def get_leaderboard_data_subq(db: Session):
    avg_subquery = (
        db.query(
            models.Rating.professor_id,
            func.avg(models.Rating.english_proficiency).label('avg_english'),
            func.avg(models.Rating.friendliness).label('avg_friendliness'),
            func.avg(models.Rating.knowledge).label('avg_knowledge')
        )
        .group_by(models.Rating.professor_id)
        .subquery()
    )

    avg_alias = aliased(avg_subquery)

    return (
        db.query(
            models.Professor.id,
            models.Professor.full_name,
            avg_alias.c.avg_english,
            avg_alias.c.avg_friendliness,
            avg_alias.c.avg_knowledge,
            ((avg_alias.c.avg_english + avg_alias.c.avg_friendliness + avg_alias.c.avg_knowledge) / 3.0).label('avg_total')
        )
        .join(avg_alias, models.Professor.id == avg_alias.c.professor_id)
        .order_by(desc('avg_total'))
        .limit(100)
        .all()
    )
