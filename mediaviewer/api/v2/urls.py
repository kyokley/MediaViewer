"""API v2 URLs"""

from django.urls import path

from . import auth_views, users_views, media_views, collections_views, additional_views

app_name = "api_v2"

urlpatterns = [
    # Authentication endpoints
    path("auth/login/", auth_views.login, name="login"),
    path("auth/login-passkey/", auth_views.login_passkey, name="login_passkey"),
    path("auth/refresh/", auth_views.refresh_token, name="refresh"),
    path("auth/logout/", auth_views.logout, name="logout"),
    path("auth/me/", auth_views.current_user, name="current_user"),
    # User endpoints
    path("users/me/", users_views.user_profile, name="user_profile"),
    path("users/me/settings/", users_views.user_settings, name="user_settings"),
    # Media endpoints
    path("movies/", media_views.list_movies, name="list_movies"),
    path("movies/<int:movie_id>/", media_views.movie_detail, name="movie_detail"),
    path("tv/", media_views.list_tv, name="list_tv"),
    path("tv/<int:tv_id>/", media_views.tv_detail, name="tv_detail"),
    path("tv/<int:tv_id>/episodes/", media_views.list_episodes, name="list_episodes"),
    path(
        "episodes/<int:episode_id>/stream/",
        media_views.get_episode_stream,
        name="get_episode_stream",
    ),
    path("genres/", media_views.list_genres, name="list_genres"),
    # Collection endpoints
    path("collections/", collections_views.list_collections, name="list_collections"),
    path(
        "collections/<int:collection_id>/",
        collections_views.collection_detail,
        name="collection_detail",
    ),
    path(
        "collections/<int:collection_id>/items/",
        collections_views.collection_items,
        name="collection_items",
    ),
    # Request endpoints
    path("requests/", additional_views.list_requests, name="list_requests"),
    path(
        "requests/<int:request_id>/",
        additional_views.request_detail,
        name="request_detail",
    ),
    path(
        "requests/<int:request_id>/vote/",
        additional_views.vote_request,
        name="vote_request",
    ),
    path(
        "requests/<int:request_id>/done/",
        additional_views.mark_request_done,
        name="mark_request_done",
    ),
    # Video progress endpoints
    path(
        "video-progress/",
        additional_views.list_video_progress,
        name="list_video_progress",
    ),
    path(
        "video-progress/<str:hashed_filename>/",
        additional_views.delete_video_progress,
        name="delete_video_progress",
    ),
    # Comment endpoints
    path("comments/", additional_views.list_comments, name="list_comments"),
    path(
        "comments/<int:comment_id>/",
        additional_views.comment_detail,
        name="comment_detail",
    ),
    # Search endpoint
    path("search/", additional_views.search, name="search"),
]
