import datetime as dt
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import aliased
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from app.crud.base import CRUDBase
from app import crud
from app.models import Reservation
from app.schemas import ReservationCreate, ReservationUpdate
from app.schemas import Reservation as ReservationSchema


class CRUDReservation(CRUDBase[Reservation, ReservationCreate, ReservationUpdate]):
    pass

reservation = CRUDReservation(Reservation)
