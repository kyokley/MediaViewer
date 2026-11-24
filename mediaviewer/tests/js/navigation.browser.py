"""Optional real-HTMX browser contract. Run directly; not collected by pytest."""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
NAVIGATION = Path(os.environ.get(
    "NAVIGATION_JS", ROOT / "mediaviewer/static/assets/navigation.js"
))
HTMX = Path(os.environ["HTMX_2_JS"])
BOOTSTRAP = Path(os.environ["BOOTSTRAP_5_JS"])
posts = []
reset_post_origins = []
history_request_started = Event()
release_history_request = Event()
delay_history_request = False
blocked_external_requests = []


def guard_browser_request(route, app_port):
    parsed = urlparse(route.request.url)
    if parsed.scheme in ("about", "data", "blob"):
        route.continue_()
        return
    if (
        parsed.scheme == "http"
        and parsed.hostname == "127.0.0.1"
        and parsed.port == app_port
    ):
        route.continue_()
        return
    blocked_external_requests.append(route.request.url)
    route.abort()


def page(path):
    name = {
        "one": "One",
        "two": "Two",
        "requests": "Requests",
        "settings": "Settings",
        "media": "Media",
        "settings-extra": "Extra",
        "player": "Player",
    }[path]
    theme = "light" if path == "one" else "dark"
    modal = ""
    if path == "settings":
        modal = """<div id="missingEmailModal" class="modal fade" tabindex="-1" aria-hidden="true">
<div class="modal-dialog"><div class="modal-content"><button id="modal-dismiss" type="button">Close</button></div></div></div>"""
    referrer_policy = "no-referrer" if path == "player" else "same-origin"
    video = '<video id="b2-video"></video>' if path == "player" else ""
    return f"""<!doctype html><html><head><meta name="referrer" content="{referrer_policy}"><meta name="htmx-config" content='{{"historyCacheSize":0,"historyRestoreAsHxRequest":false}}'><title>{name} title</title>
<script src="/bootstrap.js"></script><script src="/htmx.js"></script><script src="/navigation.js"></script>
<script>
window.lifecycle = window.lifecycle || [];
window.sharedAssets = window.sharedAssets || Array.from(document.querySelectorAll('script[src]'));
window.MediaViewerPlayer = {{init:()=>lifecycle.push('player-init:'+document.querySelector('#app-content').dataset.page+':'+document.querySelector('meta[name="referrer"]').content),
dispose:()=>lifecycle.push('dispose:'+document.querySelector('#app-content').dataset.page)}};
document.addEventListener('htmx:afterSettle',e=>lifecycle.push('settle:'+(e.detail.target&&e.detail.target.id)+':event-'+e.target.id));
document.addEventListener('htmx:historyCacheMissLoad',()=>lifecycle.push('history-load'));
document.addEventListener('htmx:historyCacheMiss',event=>{{
  if (window.__holdHistoryAbort) event.detail.xhr.abort=()=>lifecycle.push('history-abort-attempt');
}});
</script></head><body>
<div id="navigation-indicator" hidden></div><div id="navigation-error" class="hidden" hidden><span id="navigation-error-message"></span><button>dismiss</button></div>
<button id="outside-focus">Outside</button>
<div id="navigation-status"></div><div id="app-content" data-page="{path}" data-theme="{theme}" data-csrf="{path}-token" hx-boost="true" hx-target="#app-content" hx-select="#app-content" hx-swap="outerHTML" hx-history-elt hx-history="false">
<h1>{name}</h1>{video}<a id="two" href="/mediaviewer/tvshows/summary/">Two</a><a id="player" href="/mediaviewer/b2player/abcdefgh/">Player</a><a id="requests" href="/mediaviewer/requests/">Requests</a><a id="settings" href="/mediaviewer/settings/">Settings</a><a id="media" href="/mediaviewer/media/2024/file">media</a><a id="extra" href="/mediaviewer/settings/extra/">extra</a><a id="fail" href="/mediaviewer/movies/">fail</a><a id="allowed-optout" href="/mediaviewer/requests/" hx-boost="false">Requests</a>
<form id="post" method="post" action="/mediaviewer/submitsettings/"><button>Post</button></form>
<form id="unsafe" method="post" action="/mediaviewer/submitsettings-extra/"><button>Unsafe</button></form>
<form id="reset" method="post" action="/mediaviewer/user/reset/"><button>Reset</button></form>
<script>
MediaViewerNavigation.registerPageInit(() => {{
  lifecycle.push('init:{path}');
  if ('{path}' === 'settings') {{
    const node = document.getElementById('missingEmailModal');
    window.__modalNode = node;
    window.__bodyStyleBeforeModal = document.body.getAttribute('style') || '';
    window.__modalInstance = bootstrap.Modal.getOrCreateInstance(node);
    node.addEventListener('shown.bs.modal', () => lifecycle.push('modal-shown:settings'));
    node.addEventListener('hidden.bs.modal', () => lifecycle.push('modal-hidden:settings'));
    window.__modalInstance.show();
  }}
}});
</script>
{modal}
</div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/mediaviewer/movies/":
            body, status = "server error", 500
        elif self.path == "/mediaviewer/" and self.headers.get("HX-History-Restore-Request") == "true" and delay_history_request:
            history_request_started.set()
            release_history_request.wait(15)
            key = "one"
            body, status = page(key), 200
        elif self.path in ("/mediaviewer/", "/mediaviewer/tvshows/summary/", "/mediaviewer/requests/", "/mediaviewer/settings/", "/mediaviewer/media/2024/file", "/mediaviewer/settings/extra/", "/mediaviewer/b2player/abcdefgh/"):
            key = (
                "one" if self.path == "/mediaviewer/"
                else "two" if self.path.endswith("/summary/")
                else "requests" if self.path == "/mediaviewer/requests/"
                else "settings" if self.path == "/mediaviewer/settings/"
                else "media" if self.path.startswith("/mediaviewer/media/")
                else "player" if self.path.startswith("/mediaviewer/b2player/")
                else "settings-extra"
            )
            body = page(key)
            status = 200
        elif self.path == "/failure/":
            body, status = "failed", 500
        elif self.path == "/navigation.js":
            body, status = NAVIGATION.read_text(), 200
        elif self.path == "/htmx.js":
            body, status = HTMX.read_text(), 200
        elif self.path == "/bootstrap.js":
            body, status = BOOTSTRAP.read_text(), 200
        else:
            body, status = "not found", 404
        self.send_response(status)
        self.send_header("Content-Type", "text/html" if self.path not in ("/navigation.js", "/htmx.js", "/bootstrap.js") else "text/javascript")
        self.end_headers()
        try:
            self.wfile.write(body.encode())
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        posts.append(self.path)
        if self.path == "/mediaviewer/user/reset/":
            reset_post_origins.append(self.headers.get("Origin"))
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(page("two").encode())

    def log_message(self, *_):
        pass


def main():
    global delay_history_request
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=os.environ.get("CHROMIUM"))
            context = browser.new_context(service_workers="block")
            context.route("**/*", lambda route: guard_browser_request(route, server.server_port))
            page_obj = context.new_page()
            page_errors = []
            console_errors = []
            page_obj.on("pageerror", lambda error: page_errors.append(str(error)))
            page_obj.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page_obj.goto(origin + "/mediaviewer/")
            page_obj.locator("#reset button").click()
            page_obj.wait_for_load_state("domcontentloaded")
            assert reset_post_origins[-1] == origin, reset_post_origins[-1]
            page_obj.goto(origin + "/mediaviewer/")
            page_obj.evaluate("window.__navigationDocument = document.documentElement")
            page_obj.wait_for_function("lifecycle.some(x=>x==='init:one')")
            assert page_obj.locator('meta[name="referrer"]').get_attribute("content") == "same-origin"
            page_obj.locator("#two").click()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/tvshows/summary/' && lifecycle.includes('init:two')")
            assert page_obj.locator("html").get_attribute("data-bs-theme") == "dark"
            assert page_obj.title() == "Two title"
            assert page_obj.locator("#app-content").get_attribute("data-csrf") == "two-token"
            assert page_obj.evaluate("lifecycle.filter(x=>x==='init:two').length") == 1
            assert page_obj.evaluate("lifecycle.filter(x=>x==='player-init:two').length") == 0
            assert page_obj.evaluate("sharedAssets.every((node,i)=>node===document.querySelectorAll('script[src]')[i])")
            page_obj.go_back()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/' && lifecycle.filter(x=>x==='init:one').length===2")
            assert page_obj.evaluate("lifecycle.filter(x=>x==='dispose:two').length") == 1
            assert page_obj.evaluate("lifecycle.filter(x=>x==='player-init:one').length") == 0
            assert page_obj.locator("html").get_attribute("data-bs-theme") == "light"
            assert page_obj.title() == "One title"
            assert page_obj.locator("#app-content").get_attribute("data-csrf") == "one-token"
            page_obj.go_forward()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/tvshows/summary/' && lifecycle.filter(x=>x==='init:two').length===2")
            assert page_obj.evaluate("lifecycle.filter(x=>x==='dispose:one').length") == 2
            assert page_obj.title() == "Two title"
            page_obj.locator("#allowed-optout").click()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/requests/'")
            assert page_obj.evaluate("window.__navigationDocument === document.documentElement"), (
                "An allowed app route with hx-boost=false left SPA navigation"
            )
            assert page_obj.locator("#app-content").get_attribute("data-page") == "requests"
            dispose_count = page_obj.evaluate("lifecycle.filter(x=>x.startsWith('dispose:')).length")
            page_obj.locator("#fail").click()
            page_obj.wait_for_function("!document.querySelector('#navigation-error').hidden")
            assert page_obj.locator("#app-content").get_attribute("data-page") == "requests"
            assert page_obj.evaluate("lifecycle.filter(x=>x.startsWith('dispose:')).length") == dispose_count
            page_obj.locator("#extra").click()
            page_obj.wait_for_load_state("domcontentloaded")
            assert page_obj.url.endswith("/mediaviewer/settings/extra/")
            assert page_obj.locator("#app-content").get_attribute("data-page") == "settings-extra"

            modal_page_error_start = len(page_errors)
            page_obj.goto(origin + "/mediaviewer/")
            page_obj.locator("#requests").click()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/requests/'")
            page_obj.locator("#settings").click()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/settings/' && lifecycle.includes('modal-shown:settings')")
            assert page_obj.evaluate("document.body.classList.contains('modal-open')")
            assert page_obj.locator(".modal-backdrop").count() == 1
            assert page_obj.evaluate("!!document.body.style.overflow")
            modal_dispose_count = page_obj.evaluate("lifecycle.filter(x=>x==='dispose:settings').length")
            page_obj.evaluate("document.querySelector('#fail').click()")
            page_obj.wait_for_function("!document.querySelector('#navigation-error').hidden")
            assert page_obj.url.endswith("/mediaviewer/settings/")
            assert page_obj.locator(".modal-backdrop").count() == 1
            assert page_obj.evaluate("document.body.classList.contains('modal-open')")
            assert page_obj.evaluate("lifecycle.filter(x=>x==='dispose:settings').length") == modal_dispose_count
            modal_console_error_after_failed_navigation = len(console_errors)
            page_obj.go_back()
            page_obj.wait_for_function("location.pathname==='/mediaviewer/requests/' && !document.documentElement.contains(window.__modalNode)")
            assert page_obj.evaluate("lifecycle.filter(x=>x==='history-load').length") == 1
            assert page_obj.locator(".modal-backdrop").count() == 0
            assert not page_obj.evaluate("document.body.classList.contains('modal-open')")
            assert page_obj.evaluate("document.body.getAttribute('style') || ''") == page_obj.evaluate("window.__bodyStyleBeforeModal")
            assert page_obj.evaluate("bootstrap.Modal.getInstance(window.__modalNode) === null")
            page_obj.locator("#outside-focus").focus()
            assert page_obj.evaluate("document.activeElement.id === 'outside-focus'")
            page_obj.wait_for_timeout(350)
            assert page_obj.evaluate("lifecycle.filter(x=>x==='modal-hidden:settings').length") == 1
            assert page_obj.evaluate("!document.body.classList.contains('modal-open') && !document.querySelector('.modal-backdrop')")
            assert not page_errors[modal_page_error_start:], page_errors[modal_page_error_start:]
            assert not console_errors[modal_console_error_after_failed_navigation:], (
                console_errors[modal_console_error_after_failed_navigation:]
            )

            page_obj.goto(origin + "/mediaviewer/")
            page_obj.locator("#media").click()
            page_obj.wait_for_load_state("domcontentloaded")
            assert page_obj.url.endswith("/mediaviewer/media/2024/file")
            assert page_obj.locator("#app-content").get_attribute("data-page") == "media"
            page_obj.goto(origin + "/mediaviewer/")
            page_obj.locator("#post button").click()
            page_obj.wait_for_function("document.querySelector('#app-content').dataset.page==='two'")
            assert posts == [
                "/mediaviewer/user/reset/",
                "/mediaviewer/submitsettings/",
            ]
            assert page_obj.evaluate("location.pathname") == "/mediaviewer/"
            page_obj.locator("#player").click()
            page_obj.wait_for_function(
                "location.pathname==='/mediaviewer/b2player/abcdefgh/' && lifecycle.includes('player-init:player:no-referrer')"
            )
            assert page_obj.locator('meta[name="referrer"]').get_attribute("content") == "no-referrer"
            page_obj.locator("#two").click()
            page_obj.wait_for_function(
                "location.pathname==='/mediaviewer/tvshows/summary/' && lifecycle.filter(x=>x==='init:two').length>=2"
            )
            assert page_obj.locator('meta[name="referrer"]').get_attribute("content") == "same-origin"
            page_obj.go_back()
            page_obj.wait_for_function(
                "location.pathname==='/mediaviewer/b2player/abcdefgh/' && lifecycle.filter(x=>x==='player-init:player:no-referrer').length===2"
            )
            assert page_obj.locator('meta[name="referrer"]').get_attribute("content") == "no-referrer"
            page_obj.go_forward()
            page_obj.wait_for_function(
                "location.pathname==='/mediaviewer/tvshows/summary/' && lifecycle.filter(x=>x==='init:two').length>=3"
            )
            assert page_obj.locator('meta[name="referrer"]').get_attribute("content") == "same-origin"
            race_page = browser.new_page()
            race_page.on("pageerror", lambda error: page_errors.append(str(error)))
            race_page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            race_page.goto(origin + "/mediaviewer/")
            race_page.evaluate("window.__raceDocument=document.documentElement")
            race_page.locator("#two").click()
            race_page.wait_for_function("location.pathname==='/mediaviewer/tvshows/summary/' && lifecycle.includes('init:two')")
            race_page.expose_function("historyFixtureStarted", history_request_started.is_set)
            race_page_error_start = len(page_errors)
            race_console_error_start = len(console_errors)
            race_page.evaluate("window.__holdHistoryAbort=true")
            history_request_started.clear()
            release_history_request.clear()
            delay_history_request = True
            race_page.evaluate("history.back()")
            race_page.wait_for_function(
                "async () => await window.historyFixtureStarted()",
                timeout=10_000,
            )
            assert history_request_started.is_set(), "Back history request did not reach the delayed fixture"
            race_page.locator("#player").click()
            race_page.wait_for_function(
                "location.pathname==='/mediaviewer/b2player/abcdefgh/' && lifecycle.includes('player-init:player:no-referrer')"
            )
            assert race_page.evaluate("lifecycle.includes('history-abort-attempt')")
            release_history_request.set()
            race_page.wait_for_function("lifecycle.includes('history-load')")
            race_page.wait_for_timeout(100)
            assert race_page.evaluate("window.__raceDocument === document.documentElement")
            assert race_page.url.endswith("/mediaviewer/b2player/abcdefgh/")
            assert race_page.title() == "Player title"
            assert race_page.locator("#app-content").get_attribute("data-page") == "player"
            assert race_page.evaluate("lifecycle.filter(x=>x==='player-init:player:no-referrer').length") == 1
            assert race_page.evaluate("lifecycle.filter(x=>x==='dispose:player').length") == 0
            session_path = race_page.evaluate(
                "sessionStorage.getItem('htmx-current-path-for-history')"
            )
            assert session_path == "/mediaviewer/b2player/abcdefgh/"
            assert not page_errors[race_page_error_start:], page_errors[race_page_error_start:]
            assert not console_errors[race_console_error_start:], console_errors[race_console_error_start:]
            assert not blocked_external_requests, blocked_external_requests
            context.close()
            browser.close()
    finally:
        release_history_request.set()
        server.shutdown()


if __name__ == "__main__":
    main()
