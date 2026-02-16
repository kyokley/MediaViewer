"""API v2 URLs"""

from django.urls import path

from . import auth_views, users_views, media_views, collections_views

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
]
