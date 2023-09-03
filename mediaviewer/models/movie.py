from mediaviewer.media import Media, MediaManager, MediaQuerySet


class MovieQuerySet(MediaQuerySet):
    pass


class MovieManager(MediaManager):
    pass


class Movie(Media):
    objects = MovieManager.from_queryset(MovieQuerySet)()
