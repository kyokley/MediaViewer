import re
import pytest
from playwright.sync_api import Page, expect


URL = 'http://mediaviewer:8000/mediaviewer/'


def test_home_not_logged_in(page: Page):
    page.goto(URL)

    # Expect a title "to contain" a substring.
    expect(page).to_have_title(re.compile("Home - MediaViewer"))

    # create a locator
    get_started = page.get_by_role("link", name="Log In")

    # Expect an attribute "to be strictly equal" to the value.
    expect(get_started).to_have_attribute("href", "/mediaviewer/login/")

    # Click the get started link.
    get_started.click()

    # Expects the URL to contain intro.
    expect(page).to_have_url(re.compile(".*/mediaviewer/login/"))


class TestLogin:
    @pytest.fixture(autouse=True)
    def setUp(self, page):
        self.page = page

    def test_login(self):
        pass
