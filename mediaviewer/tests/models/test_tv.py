import pytest

from datetime import datetime, timedelta

from django.utils.timezone import utc


@pytest.mark.django_db
def test_episodes(create_tv,
            create_movie,
            create_tv_media_file,
            create_movie_media_file):
    tv1 = create_tv()
    tv2 = create_tv()
    hidden_tv = create_tv(hide=True)

    expected = []

    for tv in (tv1,
                tv2,
                hidden_tv):
        mf = create_tv_media_file(tv=tv)
        if tv == tv1:
            expected.append(mf)

    movie1 = create_movie()
    movie2 = create_movie()
    hidden_movie = create_movie(hide=True)

    for movie in (movie1,
                  movie2,
                  hidden_movie):
        create_movie_media_file(movie=movie)

    assert set(expected) == set(tv1.episodes())


@pytest.mark.django_db
class TestLastCreatedEpisodeAt:
    def test_last_created_episode_at(self,
                                     create_tv,
                                     create_tv_media_file):
        self.tv = create_tv()

        self.mfs = [create_tv_media_file(tv=self.tv)
                    for i in range(3)]

        dt = datetime(2018, 11, 1, 0, 0, 0, 0, utc)
        for idx, mf in enumerate(self.mfs):
            mf.date_created = dt + timedelta(days=idx)
            mf.save()

        expected = '2018-11-03T00:00:00+00:00'
        actual = self.tv.last_created_episode_at().isoformat()

        assert expected == actual

    def test_no_lastCreatedFileDate(self,
                                    create_tv):
        self.tv = create_tv()

        expected = None
        actual = self.tv.last_created_episode_at()

        assert expected == actual


@pytest.mark.django_db
def test_delete(create_tv, create_tv_media_file):
    tv = create_tv()

    tvs = [create_tv_media_file(tv=tv)
           for i in range(5)]
    tv_mp = tv.media_path

    another_tv = create_tv()
    another_tvs = [create_tv_media_file(tv=another_tv)
                   for i in range(5)]

    another_tv_mp = another_tv.media_path

    # Check for current objects' existence

    for obj in (tv, tv_mp, *tvs, another_tv, another_tv_mp, *another_tvs):
        obj.refresh_from_db()

    tv.delete()

    for obj in (tv, tv_mp, *tvs):
        with pytest.raises(obj.DoesNotExist):
            obj.refresh_from_db()

    for obj in (another_tv, another_tv_mp, *another_tvs):
        obj.refresh_from_db()
