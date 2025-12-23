from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Attendance
from app.schemas.attendance import AttendanceCreateDTO, AttendanceReadDTO

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/", response_model=AttendanceReadDTO, status_code=201)
async def record_attendance(payload: AttendanceCreateDTO, users_id: str, db: Session = Depends(get_db)):
    new_att = Attendance(
        users_id=users_id,
        competitions_id=payload.competitions_id
    )
    db.add(new_att)
    db.commit()
    db.refresh(new_att)
    return new_att

@router.get("/{user_id}", response_model=List[AttendanceReadDTO])
async def get_user_attendance(user_id: str, db: Session = Depends(get_db)):
    return db.query(Attendance).filter(Attendance.users_id == user_id).all()