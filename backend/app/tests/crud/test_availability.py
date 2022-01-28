import datetime as dt

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


from app import crud
from app.schemas import AvailabilityUpdate, AvailabilityCreate
import app.tests.utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_availability(db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    avail_in = AvailabilityCreate(
        start_date=dt.date(2022, 1, 1),
        end_date=dt.date(2022, 3, 31),
        week_day=1,
        time=dt.time(9))
    avail = await crud.availability.create(db_tests, obj_in=avail_in, speaker_id=speaker.id)
    got_avail = await crud.availability.get(db_tests, id=avail.id)
    assert got_avail.speaker_id == speaker.id
    assert got_avail.end_date == dt.date(2022, 3, 31)
    await crud.availability.remove(db_tests, id=avail.id)


async def test_update_availability(db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    avail = await crud.availability.create(
        db_tests,
        obj_in=AvailabilityCreate(
            start_date=dt.date(2022, 1, 1),
            end_date=dt.date(2022, 3, 31),
            week_day=1,
            time=dt.time(9)),
        speaker_id=speaker.id)

    avail_in = AvailabilityUpdate(end_date=dt.date(2022, 3, 15))
    await crud.availability.update(db_tests, db_obj=avail, obj_in=avail_in)
    got_avail = await crud.availability.get(db_tests, id=avail.id)
    assert got_avail.speaker_id == speaker.id
    assert got_avail.start_date == dt.date(2022, 1, 1)
    assert got_avail.end_date == dt.date(2022, 3, 15)
    await crud.availability.remove(db_tests, id=avail.id)


async def test_is_start_before_end_date() -> None:
    assert await crud.availability.is_start_before_end_date(start_date=dt.date(2021, 1, 8),
                                                            end_date=dt.date(2022, 1, 12))
    assert not await crud.availability.is_start_before_end_date(start_date=dt.date(2022, 1, 8),
                                                                end_date=dt.date(2021, 1, 12))
    assert not await crud.availability.is_start_before_end_date(start_date=dt.date(2022, 1, 8),
                                                                end_date=dt.date(2022, 1, 6))


async def test_is_a_good_weekday_int() -> None:
    startdate = dt.date(2022, 2, 2)
    assert await crud.availability.is_a_good_weekday_int(start_date=startdate, end_date=dt.date(2022, 2, 9),
                                                         weekday_int=4)
    assert await crud.availability.is_a_good_weekday_int(start_date=startdate, end_date=dt.date(2022, 2, 5),
                                                         weekday_int=5)
    assert not await crud.availability.is_a_good_weekday_int(start_date=startdate, end_date=dt.date(2022, 2, 5),
                                                             weekday_int=6)
    assert await crud.availability.is_a_good_weekday_int(start_date=startdate, end_date=dt.date(2022, 2, 2),
                                                         weekday_int=2)
    assert not await crud.availability.is_a_good_weekday_int(start_date=startdate, end_date=dt.date(2022, 2, 2),
                                                             weekday_int=0)


class TestCrudAvailabilityOne:
    """See ./CRUD_data_tests_resumes.ods -> tab "Availability" for tests data resume + drawing."""

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
                                                                               end_date=dt.date(2022, 5, 31),
                                                                               week_day=1,
                                                                               time=dt.time(9, 30)),
                                                     speaker_id=speaker1.id)

        speaker2 = await ut.create_random_speaker(db_tests, slot_time=20)
        avail1_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 1, 1),
                                                                               end_date=dt.date(2022, 3, 31),
                                                                               week_day=1,
                                                                               time=dt.time(11)),
                                                     speaker_id=speaker2.id)
        yield {"speaker1": speaker1,
               "avail1_spk1": avail1_spk1,
               "avail2_spk1": avail2_spk1,
               "avail3_spk1": avail3_spk1,
               "speaker2": speaker2,
               "avail1_spk2": avail1_spk2}
        await crud.availability.remove(db_tests, id=avail1_spk1.id)
        await crud.availability.remove(db_tests, id=avail2_spk1.id)
        await crud.availability.remove(db_tests, id=avail3_spk1.id)
        await crud.availability.remove(db_tests, id=avail1_spk2.id)

    async def test_get_by_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        spk2_id = db_avails["speaker2"].id

        avails_spk1 = await crud.availability.get_by_speaker(db_tests, spk1_id)
        av_ids_spk1 = [av.id for av in avails_spk1]
        assert (db_avails["avail1_spk1"].id
                and db_avails["avail2_spk1"].id
                and db_avails["avail3_spk1"].id) in av_ids_spk1
        assert db_avails["avail1_spk2"].id not in av_ids_spk1

        avails_spk2 = await crud.availability.get_by_speaker(db_tests, spk2_id)
        av_ids_spk2 = [av.id for av in avails_spk2]
        assert (db_avails["avail1_spk1"].id
                and db_avails["avail2_spk1"].id
                and db_avails["avail3_spk1"].id) not in av_ids_spk2
        assert db_avails["avail1_spk2"].id in av_ids_spk2

    async def test_get_all_around_date_same_weekday_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avail_thur_14_dec21 = await crud.availability\
                                        .get_all_around_date_same_weekday_speaker(db_tests, spk1_id,
                                                                                  dt.date(2021, 12, 14))
        assert len(avail_thur_14_dec21) == 1
        assert avail_thur_14_dec21[0].id == db_avails["avail3_spk1"].id

        # wednesday
        assert not await crud.availability\
                             .get_all_around_date_same_weekday_speaker(db_tests, spk1_id, dt.date(2022, 4, 6))
        # tuesday
        avail_tue_7_april = await crud.availability\
                                      .get_all_around_date_same_weekday_speaker(db_tests, spk1_id,
                                                                                dt.date(2022, 4, 7))
        assert len(avail_tue_7_april) == 1
        assert avail_tue_7_april[0].id == db_avails["avail2_spk1"].id

        # thursday
        avail_thur_8_march = await crud.availability\
                                       .get_all_around_date_same_weekday_speaker(db_tests, spk1_id,
                                                                                 dt.date(2022, 3, 8))
        assert len(avail_thur_8_march) == 2
        for av in avail_thur_8_march:
            assert av.speaker_id == spk1_id

    async def test_get_one_around_date_same_weekday_by_time_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avail_thur_14_dec21 = await crud.availability\
                                        .get_one_around_date_same_weekday_time_speaker(db_tests, spk1_id,
                                                                                       dt.date(2021, 12, 14),
                                                                                       dt.time(9, 30))
        assert avail_thur_14_dec21.id == db_avails["avail3_spk1"].id
        # thursday
        assert not await crud.availability\
                             .get_one_around_date_same_weekday_time_speaker(db_tests, spk1_id,
                                                                            dt.date(2021, 12, 14),
                                                                            dt.time(9))
        # thursday
        avail_thur_25_jan_9h30 = await crud.availability\
                                           .get_one_around_date_same_weekday_time_speaker(db_tests, spk1_id,
                                                                                          dt.date(2022, 1, 25),
                                                                                          dt.time(9, 30))
        assert avail_thur_25_jan_9h30.id == db_avails["avail3_spk1"].id
        # thursday
        avail_thur_25_jan_9h = await crud.availability\
                                         .get_one_around_date_same_weekday_time_speaker(db_tests, spk1_id,
                                                                                        dt.date(2022, 1, 25),
                                                                                        dt.time(9))
        assert avail_thur_25_jan_9h.id == db_avails["avail1_spk1"].id
        # friday
        assert not await crud.availability\
                             .get_one_around_date_same_weekday_time_speaker(db_tests, spk1_id,
                                                                            dt.date(2022, 1, 28),
                                                                            dt.time(9))

    async def test_get_times_list_by_date_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avails_times_thur_8_march = await crud.availability\
                                              .get_times_list_by_date_speaker(db_tests, spk1_id,
                                                                              dt.date(2022, 3, 8))
        assert len(avails_times_thur_8_march) == 2
        assert (dt.time(9) and dt.time(9, 30)) in avails_times_thur_8_march

    async def test_get_by_weekday_time_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        assert (await crud.availability
                          .get_by_weekday_time_speaker(db_tests, speaker_id=spk1_id,
                                                       week_day=1,
                                                       time=dt.time(9, 30)))[0].id == db_avails["avail3_spk1"].id
        # thursday
        assert (await crud.availability
                          .get_by_weekday_time_speaker(db_tests, speaker_id=spk1_id, week_day=1,
                                                       time=dt.time(9)))[0].id == db_avails["avail1_spk1"].id
        # tuesday
        assert (await crud.availability
                          .get_by_weekday_time_speaker(db_tests, speaker_id=spk1_id, week_day=3,
                                                       time=dt.time(10)))[0].id == db_avails["avail2_spk1"].id
        # tuesday
        assert not await crud.availability\
                             .get_by_weekday_time_speaker(db_tests, speaker_id=spk1_id, week_day=3, time=dt.time(11))
        # thursday
        assert not await crud.availability\
                             .get_by_weekday_time_speaker(db_tests, speaker_id=spk1_id, week_day=1, time=dt.time(11))

    async def test_get_by_weekday_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        spk2_id = db_avails["speaker2"].id
        # thursday
        thursday_avails = await crud.availability\
                                    .get_by_weekday_speaker(db_tests, speaker_id=spk1_id, week_day=1)
        assert len(thursday_avails) == 2
        av_spk_ids = [av.speaker_id for av in thursday_avails]
        assert spk1_id in av_spk_ids
        assert spk2_id not in av_spk_ids
        for av in thursday_avails:
            assert av.week_day == 1

        # tuesday
        tuesday_avails = await crud.availability\
                                   .get_by_weekday_speaker(db_tests, speaker_id=spk1_id, week_day=3)
        assert len(tuesday_avails) == 1
        assert tuesday_avails[0].speaker_id == spk1_id
        assert tuesday_avails[0].week_day == 3

        # friday
        assert not await crud.availability\
                             .get_by_weekday_speaker(db_tests, speaker_id=spk1_id, week_day=4)
        assert not await crud.availability\
                             .get_by_weekday_speaker(db_tests, speaker_id=spk2_id, week_day=4)
        # thursday
        thursday_spk2_avails = await crud.availability\
                                         .get_by_weekday_speaker(db_tests, speaker_id=spk2_id, week_day=1)
        assert len(thursday_spk2_avails) == 1
        assert thursday_spk2_avails[0].speaker_id == spk2_id
        assert thursday_spk2_avails[0].week_day == 1

    async def test_has_too_close_previous_false(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avail_in_1 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=1, time=dt.time(10))
        # thursday
        avail_in_2 = AvailabilityCreate(start_date=dt.date(2022, 1, 25), end_date=dt.date(2022, 6, 25),
                                        week_day=1, time=dt.time(8, 30))
        # friday
        avail_in_3 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=4, time=dt.time(10))
        # tuesday
        avail_in_4 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=3, time=dt.time(10, 30))
        # thursday
        avail_in_5 = AvailabilityCreate(start_date=dt.date(2022, 6, 25), end_date=dt.date(2022, 8, 25),
                                        week_day=1, time=dt.time(8, 30))

        assert not await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_1)
        assert not await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_2)
        assert not await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_3)
        assert not await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_4)
        assert not await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_5)

        spk2_id = db_avails["speaker2"].id
        # thursday
        avail_in_6 = AvailabilityCreate(start_date=dt.date(2022, 1, 25), end_date=dt.date(2022, 6, 25),
                                        week_day=1, time=dt.time(11, 20))
        # wednesday
        avail_in_7 = AvailabilityCreate(start_date=dt.date(2022, 3, 25), end_date=dt.date(2022, 6, 25),
                                        week_day=2, time=dt.time(14))
        assert not await crud.availability.has_too_close_previous(db_tests, spk2_id, obj_in=avail_in_1)
        assert not await crud.availability.has_too_close_previous(db_tests, spk2_id, obj_in=avail_in_6)
        assert not await crud.availability.has_too_close_previous(db_tests, spk2_id, obj_in=avail_in_7)

    async def test_has_too_close_previous_true(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avail_in_1 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=1, time=dt.time(9, 10))
        # thursday
        avail_in_2 = AvailabilityCreate(start_date=dt.date(2022, 1, 25), end_date=dt.date(2022, 6, 25),
                                        week_day=1, time=dt.time(9, 40))
        # tuesday
        avail_in_3 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=3, time=dt.time(10, 25))
        assert await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_1)
        assert await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_2)
        assert await crud.availability.has_too_close_previous(db_tests, spk1_id, obj_in=avail_in_3)

        spk2_id = db_avails["speaker2"].id
        # thursday
        avail_in_4 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 4, 25),
                                        week_day=1, time=dt.time(11, 15))
        assert await crud.availability.has_too_close_previous(db_tests, spk2_id, obj_in=avail_in_4)

    async def test_has_too_close_next_false(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avail_in_1 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=1, time=dt.time(10))
        # thursday
        avail_in_2 = AvailabilityCreate(start_date=dt.date(2022, 1, 25), end_date=dt.date(2022, 6, 25),
                                        week_day=1, time=dt.time(8, 30))
        # friday
        avail_in_3 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=4, time=dt.time(14))
        # tuesday
        avail_in_4 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=3, time=dt.time(9, 30))
        # thursday
        avail_in_5 = AvailabilityCreate(start_date=dt.date(2022, 7, 25), end_date=dt.date(2022, 10, 25),
                                        week_day=1, time=dt.time(10))
        assert not await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_1)
        assert not await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_2)
        assert not await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_3)
        assert not await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_4)
        assert not await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_5)

        spk2_id = db_avails["speaker2"].id
        # thursday
        avail_in_6 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 4, 25),
                                        week_day=1, time=dt.time(10, 40))
        assert not await crud.availability.has_too_close_next(db_tests, spk2_id, obj_in=avail_in_6)

    async def test_has_too_close_next_true(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        # thursday
        avail_in_1 = AvailabilityCreate(start_date=dt.date(2021, 11, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=1, time=dt.time(8, 45))
        # thursday
        avail_in_2 = AvailabilityCreate(start_date=dt.date(2022, 1, 25), end_date=dt.date(2022, 6, 25),
                                        week_day=1, time=dt.time(9, 20))
        # thursday
        avail_in_3 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 3, 25),
                                        week_day=1, time=dt.time(9, 10))
        # tuesday
        avail_in_4 = AvailabilityCreate(start_date=dt.date(2021, 12, 25), end_date=dt.date(2022, 7, 25),
                                        week_day=3, time=dt.time(9, 35))
        # tuesday
        avail_in_5 = AvailabilityCreate(start_date=dt.date(2021, 10, 25), end_date=dt.date(2022, 8, 25),
                                        week_day=3, time=dt.time(9, 50))

        assert await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_1)
        assert await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_2)
        assert await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_3)
        assert await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_4)
        assert await crud.availability.has_too_close_next(db_tests, spk1_id, obj_in=avail_in_5)

        spk2_id = db_avails["speaker2"].id
        # thursday
        avail_in_6 = AvailabilityCreate(start_date=dt.date(2022, 3, 25), end_date=dt.date(2022, 7, 25),
                                        week_day=1, time=dt.time(10, 45))
        # thursday
        avail_in_7 = AvailabilityCreate(start_date=dt.date(2021, 10, 25), end_date=dt.date(2022, 8, 25),
                                        week_day=1, time=dt.time(10, 50))
        assert await crud.availability.has_too_close_next(db_tests, spk2_id, obj_in=avail_in_6)
        assert await crud.availability.has_too_close_next(db_tests, spk2_id, obj_in=avail_in_7)


class TestCrudAvailabilityTwo:
    """See ./CRUD_data_tests_resumes.ods -> tab "Availability" for tests data resume + drawing."""

    @pytest.fixture(scope="class")
    async def db_avails(self, db_tests: AsyncSession) -> None:

        speaker1 = await ut.create_random_speaker(db_tests, slot_time=30)
        avail1_spk1 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 2, 1),
                                                                               end_date=dt.date(2022, 5, 31),
                                                                               week_day=1,
                                                                               time=dt.time(9)),
                                                     speaker_id=speaker1.id)
        avail2_spk1 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 3, 1),
                                                                               end_date=dt.date(2022, 6, 30),
                                                                               week_day=4,
                                                                               time=dt.time(14)),
                                                     speaker_id=speaker1.id)

        speaker2 = await ut.create_random_speaker(db_tests, slot_time=20)
        avail1_spk2 = await crud.availability.create(db_tests,
                                                     obj_in=AvailabilityCreate(start_date=dt.date(2022, 2, 1),
                                                                               end_date=dt.date(2022, 5, 31),
                                                                               week_day=1,
                                                                               time=dt.time(9)),
                                                     speaker_id=speaker2.id)
        yield {"speaker1": speaker1,
               "avail1_spk1": avail1_spk1,
               "avail2_spk1": avail2_spk1,
               "speaker2": speaker2,
               "avail1_spk2": avail1_spk2}
        await crud.availability.remove(db_tests, id=avail1_spk1.id)
        await crud.availability.remove(db_tests, id=avail2_spk1.id)
        await crud.availability.remove(db_tests, id=avail1_spk2.id)

    async def test_is_same_weekday_period_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        avail_in_1 = AvailabilityCreate(start_date=dt.date(2021, 12, 1), end_date=dt.date(2022, 1, 31),
                                        week_day=1, time=dt.time(9))
        avail_in_2 = AvailabilityCreate(start_date=dt.date(2022, 1, 15), end_date=dt.date(2022, 2, 28),
                                        week_day=1, time=dt.time(9))
        avail_in_3 = AvailabilityCreate(start_date=dt.date(2022, 2, 20), end_date=dt.date(2022, 4, 30),
                                        week_day=1, time=dt.time(9))
        avail_in_4 = AvailabilityCreate(start_date=dt.date(2022, 3, 15), end_date=dt.date(2022, 5, 30),
                                        week_day=1, time=dt.time(9))
        avail_in_5 = AvailabilityCreate(start_date=dt.date(2022, 6, 2), end_date=dt.date(2022, 8, 31),
                                        week_day=1, time=dt.time(9))
        avail_in_6 = AvailabilityCreate(start_date=dt.date(2021, 12, 1), end_date=dt.date(2022, 4, 30),
                                        week_day=4, time=dt.time(14))
        avail_in_7 = AvailabilityCreate(start_date=dt.date(2022, 2, 1), end_date=dt.date(2022, 8, 31),
                                        week_day=4, time=dt.time(14))
        avail_in_8 = AvailabilityCreate(start_date=dt.date(2021, 12, 1), end_date=dt.date(2022, 8, 31),
                                        week_day=3, time=dt.time(14))
        spk2_id = db_avails["speaker2"].id

        assert not await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                          obj_in=avail_in_1)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                      obj_in=avail_in_2)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                      obj_in=avail_in_3)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                      obj_in=avail_in_4)
        assert not await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                          obj_in=avail_in_5)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                      obj_in=avail_in_7)
        assert not await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk1_id,
                                                                          obj_in=avail_in_8)

        spk2_id = db_avails["speaker2"].id
        assert not await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk2_id,
                                                                          obj_in=avail_in_1)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk2_id,
                                                                      obj_in=avail_in_2)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk2_id,
                                                                      obj_in=avail_in_3)
        assert await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk2_id,
                                                                      obj_in=avail_in_4)
        assert not await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk2_id,
                                                                          obj_in=avail_in_5)

        assert not await crud.availability.is_same_weekday_period_speaker(db_tests, speaker_id=spk2_id,
                                                                          obj_in=avail_in_6)

    async def test_is_same_weekday_time_period_speaker(self, db_avails, db_tests: AsyncSession) -> None:
        spk1_id = db_avails["speaker1"].id
        avail_in_1 = AvailabilityCreate(start_date=dt.date(2021, 12, 1), end_date=dt.date(2022, 1, 31),
                                        week_day=1, time=dt.time(9))
        avail_in_2 = AvailabilityCreate(start_date=dt.date(2022, 1, 15), end_date=dt.date(2022, 2, 28),
                                        week_day=1, time=dt.time(9))
        avail_in_3 = AvailabilityCreate(start_date=dt.date(2022, 2, 20), end_date=dt.date(2022, 4, 30),
                                        week_day=1, time=dt.time(9))
        avail_in_4 = AvailabilityCreate(start_date=dt.date(2022, 3, 15), end_date=dt.date(2022, 5, 30),
                                        week_day=1, time=dt.time(9))
        avail_in_5 = AvailabilityCreate(start_date=dt.date(2022, 6, 2), end_date=dt.date(2022, 8, 31),
                                        week_day=1, time=dt.time(9))
        avail_in_6 = AvailabilityCreate(start_date=dt.date(2021, 12, 1), end_date=dt.date(2022, 4, 30),
                                        week_day=4, time=dt.time(14))
        avail_in_7 = AvailabilityCreate(start_date=dt.date(2021, 12, 1), end_date=dt.date(2022, 8, 31),
                                        week_day=4, time=dt.time(14))
        assert not await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk1_id,
                                                                               obj_in=avail_in_1)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk1_id,
                                                                           obj_in=avail_in_2)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk1_id,
                                                                           obj_in=avail_in_3)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk1_id,
                                                                           obj_in=avail_in_4)
        assert not await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk1_id,
                                                                               obj_in=avail_in_5)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk1_id,
                                                                           obj_in=avail_in_7)
        spk2_id = db_avails["speaker2"].id
        assert not await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk2_id,
                                                                               obj_in=avail_in_1)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk2_id,
                                                                           obj_in=avail_in_2)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk2_id,
                                                                           obj_in=avail_in_3)
        assert await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk2_id,
                                                                           obj_in=avail_in_4)
        assert not await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk2_id,
                                                                               obj_in=avail_in_5)
        assert not await crud.availability.is_same_weekday_time_period_speaker(db_tests, speaker_id=spk2_id,
                                                                               obj_in=avail_in_6)
