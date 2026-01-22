from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database import get_db
from app.models import Attendance
from app.schemas.attendance import AttendanceCreateDTO, AttendanceReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("attendance_router")
router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/", response_model=AttendanceReadDTO, status_code=status.HTTP_201_CREATED)
async def record_attendance(payload: AttendanceCreateDTO, users_id: str, db: Session = Depends(get_db)):
    """Registra a presença de um usuário em uma competição."""
    try:
        new_att = Attendance(
            users_id=users_id,
            competitions_id=payload.competitions_id
        )
        db.add(new_att)
        db.commit()
        db.refresh(new_att)
        
        logger.info("Presença registrada com sucesso", attendance_id=new_att.id, user_id=users_id, competition_id=payload.competitions_id)
        return new_att

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao registrar presença", error=str(e), user_id=users_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível registrar a presença no banco de dados")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao registrar presença", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.get("/{user_id}", response_model=List[AttendanceReadDTO])
async def get_user_attendance(user_id: str, db: Session = Depends(get_db)):
    """Busca todo o histórico de presença de um usuário específico."""
    try:
        attendances = db.query(Attendance).filter(Attendance.users_id == user_id).all()
        
        logger.info("Consulta de presenças do usuário realizada", user_id=user_id, count=len(attendances))
        return attendances

    except SQLAlchemyError as e:
        logger.error("Erro ao buscar presenças do usuário", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de presenças")