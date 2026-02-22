"""Tests for Collection Items API v2 endpoints"""

import pytest


@pytest.mark.django_db
class TestCollectionItemsV2:
    """Tests for /api/v2/collections/{id}/items/ endpoints"""

    @pytest.fixture(autouse=True)
    def setUp(
        self,
        client,
        create_user,
        create_collection,
        create_movie,
        create_tv,
    ):
        self.client = client
        self.user = create_user()
        self.collection = create_collection(name="Test Collection")

        # Create some movies and TV shows for testing
        self.movies = [create_movie(name=f"Movie {i}") for i in range(3)]
        self.tv_shows = [create_tv(name=f"TV Show {i}") for i in range(3)]

    def test_add_movie_to_collection_success(self):
        """Test successfully adding a movie to a collection"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {"media_id": self.movies[0].pk, "media_type": "movie"}

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 201

        json_data = resp.json()
        assert json_data["message"] == "Movie added to collection successfully"
        assert json_data["collection_id"] == self.collection.pk
        assert json_data["media_id"] == self.movies[0].pk
        assert json_data["media_type"] == "movie"

        # Verify the movie is actually in the collection
        assert self.collection in self.movies[0].collections.all()

    def test_add_tv_show_to_collection_success(self):
        """Test successfully adding a TV show to a collection"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {"media_id": self.tv_shows[0].pk, "media_type": "tv"}

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 201

        json_data = resp.json()
        assert json_data["message"] == "Tv added to collection successfully"
        assert json_data["collection_id"] == self.collection.pk
        assert json_data["media_id"] == self.tv_shows[0].pk
        assert json_data["media_type"] == "tv"

        # Verify the TV show is actually in the collection
        assert self.collection in self.tv_shows[0].collections.all()

    def test_add_movie_missing_media_id(self):
        """Test adding to collection without media_id fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {"media_type": "movie"}

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 400

        json_data = resp.json()
        assert json_data["error"]["code"] == "INVALID_DATA"
        assert "media_id is required" in json_data["error"]["message"]

    def test_add_movie_invalid_media_type(self):
        """Test adding to collection with invalid media_type fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {"media_id": self.movies[0].pk, "media_type": "invalid"}

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 400

        json_data = resp.json()
        assert json_data["error"]["code"] == "INVALID_DATA"
        assert "must be 'movie' or 'tv'" in json_data["error"]["message"]

    def test_add_nonexistent_movie(self):
        """Test adding a non-existent movie fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {
            "media_id": 99999,  # Non-existent ID
            "media_type": "movie",
        }

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 404

        json_data = resp.json()
        assert json_data["error"]["code"] == "MOVIE_NOT_FOUND"

    def test_add_nonexistent_tv_show(self):
        """Test adding a non-existent TV show fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {
            "media_id": 99999,  # Non-existent ID
            "media_type": "tv",
        }

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 404

        json_data = resp.json()
        assert json_data["error"]["code"] == "TV_NOT_FOUND"

    def test_add_to_nonexistent_collection(self):
        """Test adding to a non-existent collection fails"""
        self.client.force_login(self.user)

        url = "/mediaviewer/api/v2/collections/99999/items/"
        data = {"media_id": self.movies[0].pk, "media_type": "movie"}

        resp = self.client.post(url, data, content_type="application/json")
        assert resp.status_code == 404

        json_data = resp.json()
        assert json_data["error"]["code"] == "COLLECTION_NOT_FOUND"

    def test_get_empty_collection_items(self):
        """Test getting items from an empty collection"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["data"] == []
        assert json_data["pagination"]["total"] == 0

    def test_get_collection_items_with_movies(self):
        """Test getting items from a collection with movies"""
        self.client.force_login(self.user)

        # Add movies to collection
        self.movies[0].collections.add(self.collection)
        self.movies[1].collections.add(self.collection)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert len(json_data["data"]) == 2
        assert json_data["pagination"]["total"] == 2

        # Verify all items have media_type
        for item in json_data["data"]:
            assert "media_type" in item
            assert item["media_type"] == "movie"
            assert "name" in item or "title" in item

    def test_get_collection_items_with_tv_shows(self):
        """Test getting items from a collection with TV shows"""
        self.client.force_login(self.user)

        # Add TV shows to collection
        self.tv_shows[0].collections.add(self.collection)
        self.tv_shows[1].collections.add(self.collection)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert len(json_data["data"]) == 2
        assert json_data["pagination"]["total"] == 2

        # Verify all items have media_type
        for item in json_data["data"]:
            assert "media_type" in item
            assert item["media_type"] == "tv"

    def test_get_collection_items_mixed(self):
        """Test getting items from a collection with both movies and TV shows"""
        self.client.force_login(self.user)

        # Add both movies and TV shows to collection
        self.movies[0].collections.add(self.collection)
        self.movies[1].collections.add(self.collection)
        self.tv_shows[0].collections.add(self.collection)
        self.tv_shows[1].collections.add(self.collection)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert len(json_data["data"]) == 4
        assert json_data["pagination"]["total"] == 4

        # Count each media type
        movie_count = sum(
            1 for item in json_data["data"] if item["media_type"] == "movie"
        )
        tv_count = sum(1 for item in json_data["data"] if item["media_type"] == "tv")
        assert movie_count == 2
        assert tv_count == 2

    def test_remove_movie_from_collection_success(self):
        """Test successfully removing a movie from a collection"""
        self.client.force_login(self.user)

        # First add the movie to the collection
        self.movies[0].collections.add(self.collection)
        assert self.collection in self.movies[0].collections.all()

        # Now remove it
        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_id={self.movies[0].pk}&media_type=movie"
        resp = self.client.delete(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert "removed from collection successfully" in json_data["message"]

        # Verify the movie is no longer in the collection
        assert self.collection not in self.movies[0].collections.all()

    def test_remove_tv_show_from_collection_success(self):
        """Test successfully removing a TV show from a collection"""
        self.client.force_login(self.user)

        # First add the TV show to the collection
        self.tv_shows[0].collections.add(self.collection)
        assert self.collection in self.tv_shows[0].collections.all()

        # Now remove it
        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_id={self.tv_shows[0].pk}&media_type=tv"
        resp = self.client.delete(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert "removed from collection successfully" in json_data["message"]

        # Verify the TV show is no longer in the collection
        assert self.collection not in self.tv_shows[0].collections.all()

    def test_remove_missing_media_id(self):
        """Test removing from collection without media_id fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_type=movie"
        resp = self.client.delete(url)

        assert resp.status_code == 400
        json_data = resp.json()
        assert json_data["error"]["code"] == "INVALID_DATA"
        assert "media_id query parameter is required" in json_data["error"]["message"]

    def test_remove_invalid_media_type(self):
        """Test removing from collection with invalid media_type fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_id={self.movies[0].pk}&media_type=invalid"
        resp = self.client.delete(url)

        assert resp.status_code == 400
        json_data = resp.json()
        assert json_data["error"]["code"] == "INVALID_DATA"
        assert "must be 'movie' or 'tv'" in json_data["error"]["message"]

    def test_remove_nonexistent_movie(self):
        """Test removing a non-existent movie fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_id=99999&media_type=movie"
        resp = self.client.delete(url)

        assert resp.status_code == 404
        json_data = resp.json()
        assert json_data["error"]["code"] == "MOVIE_NOT_FOUND"

    def test_remove_nonexistent_tv_show(self):
        """Test removing a non-existent TV show fails"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_id=99999&media_type=tv"
        resp = self.client.delete(url)

        assert resp.status_code == 404
        json_data = resp.json()
        assert json_data["error"]["code"] == "TV_NOT_FOUND"

    def test_add_same_item_twice(self):
        """Test adding the same item to a collection twice (should be idempotent)"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {"media_id": self.movies[0].pk, "media_type": "movie"}

        # Add first time
        resp1 = self.client.post(url, data, content_type="application/json")
        assert resp1.status_code == 201

        # Add second time - should still succeed (idempotent)
        resp2 = self.client.post(url, data, content_type="application/json")
        assert resp2.status_code == 201

        # Verify it's only in the collection once
        assert self.movies[0].collections.filter(pk=self.collection.pk).count() == 1

    def test_unauthenticated_add_fails(self):
        """Test that unauthenticated users cannot add items"""
        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"
        data = {"media_id": self.movies[0].pk, "media_type": "movie"}

        resp = self.client.post(url, data, content_type="application/json")
        # Should return 401 or 403 (depending on authentication setup)
        assert resp.status_code in [401, 403]

    def test_unauthenticated_get_fails(self):
        """Test that unauthenticated users cannot get collection items"""
        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/"

        resp = self.client.get(url)
        # Should return 401 or 403 (depending on authentication setup)
        assert resp.status_code in [401, 403]

    def test_unauthenticated_delete_fails(self):
        """Test that unauthenticated users cannot remove items"""
        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/items/?media_id={self.movies[0].pk}&media_type=movie"

        resp = self.client.delete(url)
        # Should return 401 or 403 (depending on authentication setup)
        assert resp.status_code in [401, 403]


@pytest.mark.django_db
class TestCollectionSerializerV2:
    """Tests for Collection serializer item_count field"""

    @pytest.fixture(autouse=True)
    def setUp(
        self,
        client,
        create_user,
        create_collection,
        create_movie,
        create_tv,
    ):
        self.client = client
        self.user = create_user()
        self.collection = create_collection(name="Test Collection")
        self.movies = [create_movie(name=f"Movie {i}") for i in range(3)]
        self.tv_shows = [create_tv(name=f"TV Show {i}") for i in range(2)]

    def test_item_count_empty_collection(self):
        """Test item_count is 0 for empty collection"""
        self.client.force_login(self.user)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["item_count"] == 0

    def test_item_count_with_movies_only(self):
        """Test item_count counts movies correctly"""
        self.client.force_login(self.user)

        # Add movies to collection
        for movie in self.movies:
            movie.collections.add(self.collection)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["item_count"] == 3

    def test_item_count_with_tv_shows_only(self):
        """Test item_count counts TV shows correctly"""
        self.client.force_login(self.user)

        # Add TV shows to collection
        for tv in self.tv_shows:
            tv.collections.add(self.collection)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["item_count"] == 2

    def test_item_count_with_mixed_media(self):
        """Test item_count counts both movies and TV shows"""
        self.client.force_login(self.user)

        # Add both movies and TV shows
        for movie in self.movies:
            movie.collections.add(self.collection)
        for tv in self.tv_shows:
            tv.collections.add(self.collection)

        url = f"/mediaviewer/api/v2/collections/{self.collection.pk}/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["item_count"] == 5  # 3 movies + 2 TV shows

    def test_item_count_in_list_endpoint(self):
        """Test item_count is included in collection list endpoint"""
        self.client.force_login(self.user)

        # Add items to collection
        self.movies[0].collections.add(self.collection)
        self.tv_shows[0].collections.add(self.collection)

        url = "/mediaviewer/api/v2/collections/"
        resp = self.client.get(url)

        assert resp.status_code == 200
        json_data = resp.json()

        # Find our collection in the results
        collection_data = next(
            (c for c in json_data["data"] if c["id"] == self.collection.pk), None
        )
        assert collection_data is not None
        assert collection_data["item_count"] == 2
