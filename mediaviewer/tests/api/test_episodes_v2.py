"""Tests for episodes API endpoints"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from mediaviewer.models.tv import TV

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client"""
    return APIClient()


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    """Create authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestEpisodesEndpoint:
    """Test episodes endpoint"""

    def test_list_episodes_success(self, auth_client):
        """Test successfully listing episodes for a TV show"""
        # Get the first TV show (McMillions)
        tv_show = TV.objects.first()
        assert tv_show is not None, "No TV show found in database"

        # Make request
        url = reverse("api_v2:list_episodes", kwargs={"tv_id": tv_show.id})
        response = auth_client.get(url)

        # Assert response
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert "total_episodes" in response.data
        assert "total_seasons" in response.data

        # Verify we have seasons
        seasons = response.data["data"]
        assert len(seasons) > 0

        # Verify season structure
        first_season = seasons[0]
        assert "season_number" in first_season
        assert "episodes" in first_season
        assert len(first_season["episodes"]) > 0

        # Verify episode structure
        first_episode = first_season["episodes"][0]
        assert "id" in first_episode
        assert "season" in first_episode
        assert "episode" in first_episode
        assert "display_name" in first_episode
        assert "episode_name" in first_episode
        assert "date_created" in first_episode
        assert "watched" in first_episode

    def test_list_episodes_not_found(self, auth_client):
        """Test listing episodes for non-existent TV show"""
        url = reverse("api_v2:list_episodes", kwargs={"tv_id": 99999})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data
        assert response.data["error"]["code"] == "TV_NOT_FOUND"

    def test_list_episodes_unauthenticated(self, api_client):
        """Test listing episodes without authentication"""
        tv_show = TV.objects.first()
        if not tv_show:
            pytest.skip("No TV show found in database")

        url = reverse("api_v2:list_episodes", kwargs={"tv_id": tv_show.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
