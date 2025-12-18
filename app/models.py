from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Table, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# --- TABELAS DE ASSOCIAÇÃO (Many-to-Many) ---

competitions_has_teams = Table(
    'competitions_has_teams', Base.metadata,
    Column('competitions_id', String(36), ForeignKey('competitions.id', ondelete='CASCADE'), primary_key=True),
    Column('teams_id', String(36), ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True)
)

teams_has_users = Table(
    'teams_has_users', Base.metadata,
    Column('users_id', String(36), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('teams_id', String(36), ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True)
)

competitions_has_exercises = Table(
    'competitions_has_exercises', Base.metadata,
    Column('competitions_id', String(36), ForeignKey('competitions.id', ondelete='CASCADE'), primary_key=True),
    Column('exercises_id', String(36), ForeignKey('exercises.id', ondelete='CASCADE'), primary_key=True)
)

exercises_has_tags = Table(
    'exercises_has_tags', Base.metadata,
    Column('exercises_id', String(36), ForeignKey('exercises.id', ondelete='CASCADE'), primary_key=True),
    Column('tags_id', String(36), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

# --- MODELOS PRINCIPAIS ---

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    username = Column(String(60), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    password = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)

    teams_created = relationship("Team", back_populates="creator", cascade="all, delete-orphan")
    teams = relationship("Team", secondary=teams_has_users, back_populates="users")
    solves = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = "teams"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    creator_id = Column(String(36), ForeignKey("users.id", ondelete='CASCADE'))
    score = Column(Integer, default=0)

    creator = relationship("User", back_populates="teams_created")
    users = relationship("User", secondary=teams_has_users, back_populates="teams")
    competitions = relationship("Competition", secondary=competitions_has_teams, back_populates="teams")
    solves = relationship("Solve", back_populates="team", cascade="all, delete-orphan")

class Competition(Base):
    __tablename__ = "competitions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    organizer = Column(String(36), ForeignKey("users.id", ondelete='SET NULL'), nullable=True)
    invite_code = Column(String(20), nullable=False, unique=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default='created')

    teams = relationship("Team", secondary=competitions_has_teams, back_populates="competitions")
    exercises = relationship("Exercise", secondary=competitions_has_exercises, back_populates="competitions")
    attendances = relationship("Attendance", back_populates="competition", cascade="all, delete-orphan")
    solves = relationship("Solve", back_populates="competition", cascade="all, delete-orphan")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    difficulty = Column(String(20), nullable=False)
    flag = Column(String(256), nullable=False)
    points = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    tags = relationship("Tag", secondary=exercises_has_tags, back_populates="exercises")
    competitions = relationship("Competition", secondary=competitions_has_exercises, back_populates="exercises")
    containers = relationship("Container", back_populates="exercise", cascade="all, delete-orphan")
    solves = relationship("Solve", back_populates="exercise", cascade="all, delete-orphan")

class Container(Base):
    __tablename__ = "containers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercises_id = Column(String(36), ForeignKey("exercises.id", ondelete='CASCADE'))
    docker_id = Column(String(64))
    image_tag = Column(String(100), nullable=False)
    port = Column(Integer)
    connection = Column(String(200))
    is_active = Column(Boolean, default=True)

    exercise = relationship("Exercise", back_populates="containers")

class Solve(Base):
    __tablename__ = "solves"
    __table_args__ = (
        UniqueConstraint('users_id', 'exercises_id', 'competitions_id', name='_user_exercise_comp_uc'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(String(256))
    users_id = Column(String(36), ForeignKey("users.id", ondelete='CASCADE'))
    teams_id = Column(String(36), ForeignKey("teams.id", ondelete='SET NULL'), nullable=True)
    competitions_id = Column(String(36), ForeignKey("competitions.id", ondelete='CASCADE'))
    exercises_id = Column(String(36), ForeignKey("exercises.id", ondelete='CASCADE'))
    points_awarded = Column(Integer, nullable=False)

    user = relationship("User", back_populates="solves")
    team = relationship("Team", back_populates="solves")
    competition = relationship("Competition", back_populates="solves")
    exercise = relationship("Exercise", back_populates="solves")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)

    exercises = relationship("Exercise", secondary=exercises_has_tags, back_populates="tags")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    users_id = Column(String(36), ForeignKey("users.id", ondelete='CASCADE'))
    competitions_id = Column(String(36), ForeignKey("competitions.id", ondelete='CASCADE'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="attendances")
    competition = relationship("Competition", back_populates="attendances")