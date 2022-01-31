import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.utils import from_weekday_int_to_str
from app.tests import utils as ut
from app import crud
from app.schemas import AvailabilityCreate, AvailabilityUpdate

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


class TestEndpointsAvailabilities:
    """See ./ENDPOINTS_data_tests_resumes.ods -> tab "Availability" for tests data resume + drawing."""

    @pytest.fixture(scope="class")
    async def db_avails(self, db_tests: AsyncSession) -> None:

        speaker1 = await ut.create_random_speaker(db_tests, slot_time=30)
        avail1_spk1 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 1, 1),
                                                                               end_date=dt.date(2022, 3, 31),
                                                                               week_day=1,
                                                                               time=dt.time(9)),
                                                     speaker_id=speaker1.id)
        avail2_spk1 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2021, 12, 1),
                                                                               end_date=dt.date(2022, 5, 31),
                                                                               week_day=3,
                                                                               time=dt.time(10)),
                                                     speaker_id=speaker1.id)
        avail3_spk1 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2021, 12, 1),
                                                                               end_date=dt.date(2022, 6, 15),
                                                                               week_day=1,
                                                                               time=dt.time(9, 30)),
                                                     speaker_id=speaker1.id)
        avail4_spk1 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 3, 1),
                                                                               end_date=dt.date(2022, 8, 31),
                                                                               week_day=4,
                                                                               time=dt.time(14)),
                                                     speaker_id=speaker1.id)

        speaker2 = await ut.create_random_speaker(db_tests, slot_time=20)
        avail1_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 1, 1),
                                                                               end_date=dt.date(2022, 3, 31),
                                                                               week_day=1,
                                                                               time=dt.time(11)),
                                                     speaker_id=speaker2.id)
        avail2_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2021, 11, 15),
                                                                               end_date=dt.date(2022, 4, 30),
                                                                               week_day=1,
                                                                               time=dt.time(11, 20)),
                                                     speaker_id=speaker2.id)
        avail3_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 4, 1),
                                                                               end_date=dt.date(2022, 8, 31),
                                                                               week_day=5,
                                                                               time=dt.time(11, 30)),
                                                     speaker_id=speaker2.id)
        avail4_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 2, 15),
                                                                               end_date=dt.date(2022, 9, 30),
                                                                               week_day=5,
                                                                               time=dt.time(12, 30)),
                                                     speaker_id=speaker2.id)
        avail5_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 2, 18),
                                                                               end_date=dt.date(2022, 2, 18),
                                                                               week_day=4,
                                                                               time=dt.time(14, 30)),
                                                     speaker_id=speaker2.id)
        yield {"speaker1": speaker1,
               "avail1_spk1": avail1_spk1,
               "avail2_spk1": avail2_spk1,
               "avail3_spk1": avail3_spk1,
               "avail4_spk1": avail4_spk1,
               "speaker2": speaker2,
               "avail1_spk2": avail1_spk2,
               "avail2_spk2": avail2_spk2,
               "avail3_spk2": avail3_spk2,
               "avail4_spk2": avail4_spk2,
               "avail5_spk2": avail5_spk2}
        await crud.availability.remove(db_tests, id=avail1_spk1.id)
        await crud.availability.remove(db_tests, id=avail2_spk1.id)
        await crud.availability.remove(db_tests, id=avail3_spk1.id)
        await crud.availability.remove(db_tests, id=avail4_spk1.id)
        await crud.availability.remove(db_tests, id=avail1_spk2.id)
        await crud.availability.remove(db_tests, id=avail2_spk2.id)
        await crud.availability.remove(db_tests, id=avail3_spk2.id)
        await crud.availability.remove(db_tests, id=avail4_spk2.id)

    async def test_read_availabilities_mine_by_speaker(self, async_client: AsyncClient,
                                                       db_tests: AsyncSession, db_avails) -> None:
        spk1 = db_avails["speaker1"]
        speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client,
                                                                                 email=spk1.email, db=db_tests)
        r = await async_client.get(f"{settings.API_V1_STR}/availabilities/mine", headers=speaker_token_headers)
        r_avails = r.json()
        assert len(r_avails) == 4, ("Each availability that is created during a test method "
                                    "(i.e not by db_avails fixture) has to be deleted at the end of the test...")
        for av in r_avails:
            assert av["speaker_id"] == spk1.id

    async def test_read_availabilities_mine_by_not_speaker(self, async_client: AsyncClient,
                                                           admin_token_headers: dict[str, str]) -> None:
        """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
        r = await async_client.get(f"{settings.API_V1_STR}/availabilities/mine", headers=admin_token_headers)
        assert r.status_code == 400
        assert "To do this, the user has to be a Speaker user" in r.json().values()

    async def test_read_availabilities_by_speaker_id_not_set_by_speaker(self, async_client: AsyncClient,
                                                                        db_tests: AsyncSession, db_avails) -> None:
        spk1 = db_avails["speaker1"]
        speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client,
                                                                                 email=spk1.email, db=db_tests)
        r = await async_client.get(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers)
        r_avails = r.json()
        assert len(r_avails) == 4, ("Each availability that is created during a test method "
                                    "(i.e not by db_avails fixture) has to be deleted at the end of the test...")
        for av in r_avails:
            assert av["speaker_id"] == spk1.id

    async def test_read_availabilities_by_speaker_id_not_set_by_participant(self, async_client: AsyncClient,
                                                                            db_tests: AsyncSession, db_avails) -> None:
        spk1 = db_avails["speaker1"]
        participant = await ut.create_random_participant(db_tests, speaker_id=spk1.id)
        participant_token_headers = await ut.participant_authentication_token_from_email(client=async_client,
                                                                                         email=participant.email,
                                                                                         db=db_tests)
        r = await async_client.get(f"{settings.API_V1_STR}/availabilities", headers=participant_token_headers)
        r_avails = r.json()
        assert len(r_avails) == 4, ("Each availability that is created during a test method "
                                    "(i.e not by db_avails fixture) has to be deleted at the end of the test...")
        for av in r_avails:
            assert av["speaker_id"] == spk1.id
        await crud.participant.remove(db_tests, id=participant.id)

    async def test_read_availabilities_by_speaker_id_set_by_participant(self, async_client: AsyncClient,
                                                                        db_tests: AsyncSession, db_avails) -> None:
        spk2 = db_avails["speaker2"]
        participant = await ut.create_random_participant(db_tests)
        participant_token_headers = await ut.participant_authentication_token_from_email(client=async_client,
                                                                                         email=participant.email,
                                                                                         db=db_tests)
        r = await async_client.get(f"{settings.API_V1_STR}/availabilities", params={"speaker_id": spk2.id},
                                   headers=participant_token_headers)
        r_avails = r.json()
        assert len(r_avails) == 5, ("Each availability that is created during a test method "
                                    "(i.e not by db_avails fixture) has to be deleted at the end of the test...")
        for av in r_avails:
            assert av["speaker_id"] == spk2.id

    async def test_read_availabilities_by_speaker_id_set_not_exists_by_participant(self, async_client: AsyncClient,
                                                                                   db_tests: AsyncSession) -> None:
        participant = await ut.create_random_participant(db_tests)
        # get a not existing speaker id
        db_speakers = await crud.speaker.get_multi(db_tests)
        if db_speakers:
            max_id = max([speaker.id for speaker in db_speakers])
        else:
            max_id = 0
        participant_token_headers = await ut.participant_authentication_token_from_email(client=async_client,
                                                                                         email=participant.email,
                                                                                         db=db_tests)
        r = await async_client.get(f"{settings.API_V1_STR}/availabilities", params={"speaker_id": max_id + 1},
                                   headers=participant_token_headers)
        assert r.status_code == 404
        assert "A speaker with this id does not exist in the system..." in r.json().values()

    async def test_create_availability_by_not_speaker(self, async_client: AsyncClient,
                                                      admin_token_headers: dict[str, str]) -> None:
        """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date.today(),
                                                   end_date=(dt.date.today() + dt.timedelta(days=10)),
                                                   week_day=0, time=dt.time(10)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=admin_token_headers, json=data)
        assert r.status_code == 400
        assert "To do this, the user has to be a Speaker user" in r.json().values()

    async def test_create_availability_enddate_before_startdate(self, async_client: AsyncClient,
                                                                speaker_token_headers: dict[str, str]) -> None:
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date.today(),
                                                   end_date=(dt.date.today() - dt.timedelta(days=1)),
                                                   week_day=0, time=dt.time(10)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers, json=data)
        assert r.status_code == 400
        assert "Cannot create availability with end_date before start_date..." in r.json().values()

    async def test_create_availability_with_wrong_weekday(self, async_client: AsyncClient,
                                                          speaker_token_headers: dict[str, str]) -> None:
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date(2022, 2, 2), end_date=dt.date(2022, 2, 6),
                                                   week_day=0, time=dt.time(10)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers, json=data)
        assert r.status_code == 400
        assert (f"Cannot create availability because {data['week_day']} "
                f"= {from_weekday_int_to_str(data['week_day'])} a weekday that does not exists "
                f"between {data['start_date']} and {data['end_date']}.") in r.json().values()

    async def test_create_availability_same_period_weekday_time_exists(self, async_client: AsyncClient,
                                                                       db_tests: AsyncSession, db_avails) -> None:
        spk1 = db_avails["speaker1"]
        speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client,
                                                                                 email=spk1.email, db=db_tests)
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date(2021, 12, 15), end_date=dt.date(2022, 2, 18),
                                                   week_day=1, time=dt.time(9)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers, json=data)
        assert r.status_code == 400
        assert (f"Sorry, cannot create because at least one availability already exists on a "
                f"{from_weekday_int_to_str(data['week_day'])} at "
                f"{data['time']} between {data['start_date']} and {data['end_date']}.") in r.json().values()

    async def test_create_availability_has_too_close_previous(self, async_client: AsyncClient, db_tests: AsyncSession,
                                                              db_avails) -> None:
        spk1 = db_avails["speaker1"]
        speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client, email=spk1.email,
                                                                                 db=db_tests)
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date(2021, 12, 15), end_date=dt.date(2022, 5, 15),
                                                   week_day=1, time=dt.time(9, 15)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers, json=data)
        assert r.status_code == 400
        assert (f"Sorry, cannot create because at least one availability already exists on a "
                f"{from_weekday_int_to_str(data['week_day'])} "
                f"between {data['start_date']} and {data['end_date']} "
                f"at an earlier time but that overlaps {data['time']} "
                f"because of duration = {spk1.slot_time} minutes.") in r.json().values()

    async def test_create_availability_has_too_close_next(self, async_client: AsyncClient, db_tests: AsyncSession,
                                                          db_avails) -> None:
        spk2 = db_avails["speaker2"]
        speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client, email=spk2.email,
                                                                                 db=db_tests)
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date(2022, 1, 15), end_date=dt.date(2022, 2, 18),
                                                   week_day=4, time=dt.time(14, 15)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers, json=data)
        assert r.status_code == 400
        assert (f"Sorry, cannot create because at least one availability already exists on a "
                f"{from_weekday_int_to_str(data['week_day'])} "
                f"between {data['start_date']} and {data['end_date']} "
                f"at a later time than {data['time']} but that would be overlapped "
                f"because of duration = {spk2.slot_time} minutes.") in r.json().values()

    async def test_create_availability(self, async_client: AsyncClient, db_tests: AsyncSession, db_avails) -> None:
        spk1 = db_avails["speaker1"]
        speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client, email=spk1.email,
                                                                                 db=db_tests)
        data = jsonable_encoder(AvailabilityCreate(start_date=dt.date(2022, 6, 16), end_date=dt.date(2022, 8, 31),
                                                   week_day=1, time=dt.time(9, 30)))
        r = await async_client.post(f"{settings.API_V1_STR}/availabilities", headers=speaker_token_headers, json=data)
        assert r.status_code == 200, f"{r.json()}"
        r_avail = r.json()
        assert spk1.id in r_avail.values()
        await crud.availability.remove(db_tests, id=r_avail["id"])
