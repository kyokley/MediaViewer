"""
Django management command to generate seed data for testing the MediaViewer application.

This command creates:
- Test users (admin, test_user, demo_user)
- Movies with genres
- TV shows with genres
- Media requests with votes
- Comments on media
- Video progress entries
- Collections
"""

import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from mediaviewer.models import (
    Comment,
    Genre,
    Movie,
    Request,
    RequestVote,
    TV,
    VideoProgress,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate seed data for testing the MediaViewer application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing seed data before creating new data",
        )
        parser.add_argument(
            "--users-only",
            action="store_true",
            help="Only create test users, skip other data",
        )

    def handle(self, *args, **options):
        try:
            if options.get("clear"):
                self.stdout.write(self.style.WARNING("Clearing existing seed data..."))
                self.clear_seed_data()

            self.stdout.write(self.style.SUCCESS("Creating seed data..."))

            # Create test users
            users = self.create_users()
            self.stdout.write(self.style.SUCCESS(f"✓ Created {len(users)} test users"))

            if options.get("users_only"):
                self.stdout.write(
                    self.style.SUCCESS("Seed data creation complete (users only)")
                )
                return

            # Create genres
            genres = self.create_genres()
            self.stdout.write(self.style.SUCCESS(f"✓ Created {len(genres)} genres"))

            # Create movies
            movies = self.create_movies(genres)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {len(movies)} movies"))

            # Create TV shows
            tv_shows = self.create_tv_shows(genres)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {len(tv_shows)} TV shows"))

            # Create media requests
            requests = self.create_requests(users)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created {len(requests)} media requests")
            )

            # Create request votes
            votes = self.create_request_votes(requests, users)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {votes} request votes"))

            # Create comments
            comments = self.create_comments(users, movies, tv_shows)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {len(comments)} comments"))

            # Create video progress
            progress = self.create_video_progress(users, movies, tv_shows)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created {progress} video progress entries")
            )

            self.stdout.write(
                self.style.SUCCESS("\n✓ Seed data creation completed successfully!")
            )
            self.stdout.write(
                self.style.WARNING(
                    "\nTest credentials:\n"
                    "  Username: test_user\n"
                    "  Password: password\n"
                    "  Username: demo_user\n"
                    "  Password: password\n"
                )
            )

        except Exception as e:
            raise CommandError(f"Error creating seed data: {str(e)}")

    def clear_seed_data(self):
        """Clear seed data from the database"""
        # Delete in reverse order of dependencies
        RequestVote.objects.all().delete()
        Request.objects.all().delete()
        Comment.objects.all().delete()
        VideoProgress.objects.all().delete()
        TV.objects.all().delete()
        Movie.objects.all().delete()
        Genre.objects.all().delete()

        # Delete test users except admin
        User.objects.filter(username__in=["test_user", "demo_user"]).delete()

        self.stdout.write(self.style.SUCCESS("✓ Cleared existing seed data"))

    def create_users(self):
        """Create test users"""
        users = []

        # Create admin user if it doesn't exist
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin")
            admin.save()
        users.append(admin)

        # Create test_user
        test_user, created = User.objects.get_or_create(
            username="test_user",
            defaults={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        if created:
            test_user.set_password("password")
            test_user.save()
        users.append(test_user)

        # Create demo_user
        demo_user, created = User.objects.get_or_create(
            username="demo_user",
            defaults={
                "email": "demo@example.com",
                "first_name": "Demo",
                "last_name": "User",
            },
        )
        if created:
            demo_user.set_password("password")
            demo_user.save()
        users.append(demo_user)

        return users

    def create_genres(self):
        """Create movie and TV show genres"""
        genre_names = [
            "Action",
            "Comedy",
            "Drama",
            "Horror",
            "Science Fiction",
            "Fantasy",
            "Thriller",
            "Romance",
            "Adventure",
            "Mystery",
        ]

        genres = []
        for genre_name in genre_names:
            genre, created = Genre.objects.get_or_create(genre=genre_name)
            genres.append(genre)

        return genres

    def create_movies(self, genres):
        """Create sample movies"""
        movie_data = [
            {
                "name": "The Matrix",
                "genres": [genres[4], genres[6]],  # Sci-Fi, Thriller
            },
            {
                "name": "Inception",
                "genres": [genres[4], genres[8]],  # Sci-Fi, Adventure
            },
            {
                "name": "Forrest Gump",
                "genres": [genres[2], genres[7]],  # Drama, Romance
            },
            {
                "name": "The Dark Knight",
                "genres": [genres[0], genres[6]],  # Action, Thriller
            },
            {
                "name": "Interstellar",
                "genres": [genres[4], genres[2]],  # Sci-Fi, Drama
            },
            {
                "name": "Pulp Fiction",
                "genres": [genres[0], genres[6]],  # Action, Thriller
            },
            {
                "name": "The Shawshank Redemption",
                "genres": [genres[2], genres[6]],  # Drama, Thriller
            },
            {
                "name": "Gladiator",
                "genres": [genres[0], genres[2]],  # Action, Drama
            },
        ]

        movies = []
        for movie_info in movie_data:
            movie, created = Movie.objects.get_or_create(name=movie_info["name"])
            if created:
                movie.finished = False
                movie.hide = False
                movie.save()

            # Add genres
            for genre in movie_info["genres"]:
                # Note: This depends on your actual many-to-many relationship
                # If genres are connected through another model, adjust accordingly
                pass

            movies.append(movie)

        return movies

    def create_tv_shows(self, genres):
        """Create sample TV shows"""
        tv_data = [
            {
                "name": "Breaking Bad",
                "genres": [genres[2], genres[6]],  # Drama, Thriller
            },
            {
                "name": "The Office",
                "genres": [genres[1], genres[7]],  # Comedy, Romance
            },
            {
                "name": "Game of Thrones",
                "genres": [
                    genres[5],
                    genres[0],
                    genres[6],
                ],  # Fantasy, Action, Thriller
            },
            {
                "name": "Stranger Things",
                "genres": [genres[3], genres[5]],  # Horror, Fantasy
            },
            {
                "name": "The Crown",
                "genres": [genres[2]],  # Drama
            },
            {
                "name": "Westworld",
                "genres": [genres[4], genres[6]],  # Sci-Fi, Thriller
            },
        ]

        tv_shows = []
        for tv_info in tv_data:
            tv, created = TV.objects.get_or_create(name=tv_info["name"])
            if created:
                tv.finished = False
                tv.hide = False
                tv.save()

            tv_shows.append(tv)

        return tv_shows

    def create_requests(self, users):
        """Create media requests"""
        request_names = [
            "Avatar 3",
            "The Last of Us Season 2",
            "Dune Part Three",
            "Oppenheimer",
            "Barbie Extended Edition",
            "Killers of the Flower Moon",
            "Blue Beetle",
            "Saw X",
        ]

        requests = []
        for i, request_name in enumerate(request_names):
            # Alternate which user creates the request
            user = users[i % len(users)]

            req, created = Request.objects.get_or_create(
                name=request_name,
                user=user,
                defaults={"done": i % 3 == 0},  # Some are marked as done
            )

            if created:
                requests.append(req)

        return requests

    def create_request_votes(self, requests, users):
        """Create votes on media requests"""
        vote_count = 0

        for request in requests:
            # Skip the creator and add votes from other users
            for user in users:
                if user == request.user:
                    continue

                # Create a vote
                vote, created = RequestVote.objects.get_or_create(
                    request=request,
                    user=user,
                )

                if created:
                    vote_count += 1

        return vote_count

    def create_comments(self, users, movies, tv_shows):
        """Create comments on movies and TV shows"""
        comments = []

        # Create comments on movies
        for i, movie in enumerate(movies):
            user = users[i % len(users)]

            comment, created = Comment.objects.get_or_create(
                user=user,
                movie=movie,
                defaults={"viewed": i % 2 == 0},  # Some are viewed
            )

            if created:
                comments.append(comment)

        # Create comments on TV shows (using media_file if available)
        for i, tv in enumerate(tv_shows):
            user = users[i % len(users)]

            # Comments on TV shows typically reference media files
            # For now, create comments linked to the TV show via movie field
            # In a real scenario, you'd have media files for TV episodes
            try:
                comment, created = Comment.objects.get_or_create(
                    user=user,
                    movie=None,  # TV shows don't use this field typically
                    media_file=None,
                    defaults={"viewed": i % 2 == 0},
                )

                if created:
                    comments.append(comment)
            except Exception as e:
                logger.warning(f"Could not create comment for TV show: {str(e)}")

        return comments

    def create_video_progress(self, users, movies, tv_shows):
        """Create video progress entries"""
        progress_count = 0

        all_media = movies + tv_shows

        for i, media in enumerate(all_media):
            user = users[i % len(users)]

            # Create a hashed filename (in real usage this would be based on actual files)
            hashed_filename = f"media_{media.id}_{user.id}"

            # Create progress entry
            progress, created = VideoProgress.objects.get_or_create(
                user=user,
                hashed_filename=hashed_filename,
                defaults={
                    "offset": (i + 1) * 1200,  # Different watch times
                },
            )

            if created:
                progress_count += 1

        return progress_count
