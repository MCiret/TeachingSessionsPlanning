from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.utils import from_weekday_int_to_str

router = APIRouter()


@router.get("/mine", response_model=list[schemas.Availability])
async def read_availabilities_mine(
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_active_speaker_user),
) -> Any:
    """
    Read all current speaker availabilities.
    **Allowed for speaker user only.**
    """
    return await crud.availability.get_by_speaker(db, speaker_id=current_user.id)


@router.get("", response_model=list[schemas.Availability])
async def read_availabilities_by_speaker(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    speaker_id: int = None,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_participant_user),
) -> Any:
    """
    Read all availabilities for the current speaker or current participant's speaker (if speaker_id is not set).
    Read all availabilities for the speaker whose id is set as speaker_id param.
    **Allowed for speaker or participant user only.**
    """
    if speaker_id is None:
        if await crud.user.is_speaker(current_user):
            speaker_id = current_user.id
        elif await crud.user.is_participant(current_user):
            speaker_id = current_user.speaker_id
    else:
        if not await crud.speaker.get(db, id=speaker_id):
            raise HTTPException(
                status_code=404,
                detail="A speaker with this id does not exist in the system...",
            )
    return await crud.availability.get_by_speaker(db, speaker_id=speaker_id)


@router.post("", response_model=schemas.Availability)
async def create_availability(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    avail_in: schemas.AvailabilityCreate,
    current_user: models.User = Depends(deps.get_current_active_speaker_user)
) -> Any:
    """
    Create new availability for current speaker user.
    **Allowed for speaker user only.**
    """
    if not await crud.availability.is_start_before_end_date(avail_in.start_date, avail_in.end_date):
        raise HTTPException(
                    status_code=400,
                    detail=("Cannot create availability with end_date before start_date...")
                )
    if not await crud.availability.is_a_good_weekday_int(avail_in.start_date, avail_in.end_date, avail_in.week_day):
        raise HTTPException(
                    status_code=400,
                    detail=(f"Cannot create availability because {avail_in.week_day} "
                            f"= {from_weekday_int_to_str(avail_in.week_day)} a weekday that does not exists "
                            f"between {avail_in.start_date} and {avail_in.end_date}.")
                )
    if await crud.availability.is_same_period_weekday_time_exists(db, speaker_id=current_user.id, obj_in=avail_in):
        raise HTTPException(
                    status_code=400,
                    detail=(f"Sorry, cannot create because at least one availability already exists on a "
                            f"{from_weekday_int_to_str(avail_in.week_day)} at "
                            f"{avail_in.time} between {avail_in.start_date} and {avail_in.end_date}.")
                )
    if await crud.availability.has_too_close_previous(db, current_user.id, avail_in):
        raise HTTPException(
                    status_code=400,
                    detail=(f"Sorry, cannot create because at least one availability already exists on a "
                            f"{from_weekday_int_to_str(avail_in.week_day)} "
                            f"between {avail_in.start_date} and {avail_in.end_date} "
                            f"at an earlier time but that overlaps {avail_in.time} "
                            f"because of duration = {current_user.slot_time} minutes.")
                )
    if await crud.availability.has_too_close_next(db, current_user.id, avail_in):
        raise HTTPException(
                    status_code=400,
                    detail=(f"Sorry, cannot create because at least one availability already exists on a "
                            f"{from_weekday_int_to_str(avail_in.week_day)} "
                            f"between {avail_in.start_date} and {avail_in.end_date} "
                            f"at a later time than {avail_in.time} but that would be overlapped "
                            f"because of duration = {current_user.slot_time} minutes.")
                )
    return await crud.availability.create(db, obj_in=avail_in, speaker_id=current_user.id)
