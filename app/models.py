from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# USERS, TEAMS AND COMPETITIONS

class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(60), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    password = Column(String(256), nullable=False)
    phone_number = Column(String(20), nullable=True)
    is_admin = Column(Boolean, default=False)

    solves = relationship("Solve", back_populates="user")

class Team(Base):
    __tablename__ = 'teams'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    competition_id = Column(String(36), ForeignKey('competitions.id'), nullable=False)
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False)

    score = Column(Integer, default=0)

    solves = relationship("Solve", back_populates="team")
    competition = relationship("Competition", back_populates="teams")

class Competition(Base):
    __tablename__ = 'competitions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    organizer = Column(String(100), nullable=False)
    invite_code = Column(String(20), nullable=False, unique=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default='created')

    teams = relationship("Team", back_populates="competition")


# CTF FOCUSED

class Exercise(Base):
    __tablename__ = 'exercises'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)

    flag = Column(String(256), nullable=False)
    points = Column(Integer, nullable=False)

    image_tag = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True)

    containers = relationship("Container", back_populates="exercise")
    solves = relationship("Solve", back_populates="exercise")

class Container(Base):
    __tablename__ = 'containers'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String(36), ForeignKey('exercises.id'), nullable=False)
    
    container_docker_id = Column(String(64), nullable=True)
    image_tag = Column(String(100), nullable=False)
    
    port_public = Column(Integer, nullable=False)
    connection_command = Column(String(200), nullable=True) # Ex: "nc 192.168.1.5 1337" ou link http
    
    is_active = Column(Boolean, default=True)
    
    exercise = relationship("Exercise", back_populates="containers")

class Solve(Base):
    __tablename__ = 'solves'

    # Evita race condition
    __table_args__ = (
        UniqueConstraint('team_id', 'exercise_id', name='_team_exercise_uc'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    submission_content = Column(String(256), nullable=True)

    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    team_id = Column(String(36), ForeignKey('teams.id'), nullable=False)
    
    exercise_id = Column(String(36), ForeignKey('exercises.id'), nullable=False)
    
    points_awarded = Column(Integer, nullable=False)
    
    user = relationship("User", back_populates="solves")
    team = relationship("Team", back_populates="solves")
    exercise = relationship("Exercise", back_populates="solves")


# AUXILIARY AND RELATIONAL TABLES
class Tag(Base):
    __tablename__ = 'tags'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(50), nullable=False, unique=True)

class UserCompetition(Base):
    __tablename__ = 'user_competitions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    competition_id = Column(String(36), ForeignKey('competitions.id'), nullable=False)

class UserTeam(Base):
    __tablename__ = 'user_teams'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    team_id = Column(String(36), ForeignKey('teams.id'), nullable=False)

class ExerciseTag(Base):
    __tablename__ = 'exercise_tags'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String(36), ForeignKey('exercises.id'), nullable=False)
    tag_id = Column(String(36), ForeignKey('tags.id'), nullable=False)

class ExerciseCompetition(Base):
    __tablename__ = 'exercise_competitions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String(36), ForeignKey('exercises.id'), nullable=False)
    competition_id = Column(String(36), ForeignKey('competitions.id'), nullable=False)