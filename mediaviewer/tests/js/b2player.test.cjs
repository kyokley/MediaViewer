const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "../../static/assets/b2player.js"), "utf8");
const styles = fs.readFileSync(path.join(__dirname, "../../static/assets/b2player.css"), "utf8");
const template = fs.readFileSync(path.join(__dirname, "../../templates/mediaviewer/b2player.html"), "utf8");
const tick = async () => { for (let index = 0; index < 12; index += 1) await Promise.resolve(); };
const deferred = () => {
    let resolve;
    let reject;
    const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
    return { promise, resolve, reject };
};

function createPlayer(fetcher = async () => ({ ok: true, json: async () => ({ offset: null }) }), configPatch = {}) {
    const ids = ["player-status", "seek-back", "seek-forward", "start-over", "binge-toggle", "cast-video", "airplay-video"];
    const elements = Object.fromEntries(ids.map((id) => [id, {
        id, textContent: "", attributes: id === "player-status" ? { "data-loading": "true" } : {}, listeners: {}, hidden: ["airplay-video", "cast-video"].includes(id), style: {},
        classes: new Set(),
        classList: { toggle(name, enabled) { enabled ? this.owner.classes.add(name) : this.owner.classes.delete(name); } },
        addEventListener(type, fn) { this.listeners[type] = fn; },
        setAttribute(name, value) { this.attributes[name] = value; },
        removeAttribute(name) { delete this.attributes[name]; },
        click() { return this.listeners.click?.(); },
    }]));
    for (const element of Object.values(elements)) element.classList.owner = element;
    const listeners = new Map();
    const textTrackListeners = {};
    const textTracks = {
        tracks: [], length: 0,
        addEventListener(type, fn) { textTrackListeners[type] = fn; },
        item(index) { return this.tracks[index] || null; },
        dispatch(type) { textTrackListeners[type]?.(); },
        add(track) { this.tracks.push(track); this.length = this.tracks.length; this[this.length - 1] = track; },
        remove(track) {
            this.tracks = this.tracks.filter((item) => item !== track);
            this.length = this.tracks.length;
            for (let index = 0; index < this.length; index += 1) this[index] = this.tracks[index];
            delete this[this.length];
        },
    };
    const retryButton = { listeners: {}, addEventListener(type, fn) { this.listeners[type] = fn; }, click() { return this.listeners.click?.(); } };
    Object.defineProperty(elements["player-status"], "innerHTML", {
        set(value) {
            this._html = value;
            this.textContent = value.match(/class="visually-hidden">([^<]*)<\/span>/)?.[1] || value.replace(/<[^>]*>/g, "");
        },
        get() { return this._html; },
    });
    const video = {
        currentTime: 0, duration: 100, paused: true, readyState: 0, children: [], loadCalls: 0,
        textTracks,
        append(child) {
            child.remove = () => {
                this.children = this.children.filter((item) => item !== child);
                if (child.track) textTracks.remove(child.track);
            };
            this.children.push(child);
            if (child.tagName === "track") {
                child.track = { kind: child.kind, mode: "disabled", label: child.label, language: child.srclang };
                textTracks.add(child.track);
            }
        },
        querySelector(tag) { return this.children.find((child) => child.tagName === tag); },
        querySelectorAll(selector) { return this.children.filter((child) => selector.split(", ").includes(child.tagName)); },
        addEventListener(type, fn, options = {}) { const entries = listeners.get(type) || []; entries.push({ fn, once: options.once }); listeners.set(type, entries); },
        dispatch(type, event = {}) {
            if (type === "play") this.paused = false;
            if (type === "pause" || type === "ended") this.paused = true;
            if (type === "ended") this.currentTime = this.duration;
            const entries = listeners.get(type) || [];
            for (const entry of [...entries]) {
                entry.fn(event);
                if (entry.once) entries.splice(entries.indexOf(entry), 1);
            }
        },
        pause() { this.paused = true; this.dispatch("pause"); },
        load() { this.loadCalls += 1; queueMicrotask(() => textTracks.dispatch("change")); },
    };
    if (configPatch.airplaySupported) {
        video.pickerCalls = 0;
        video.webkitShowPlaybackTargetPicker = () => { video.pickerCalls += 1; };
    }
    elements["b2-video"] = video;
    elements["b2-player-config"] = { textContent: JSON.stringify({
        media_url: "/media", progress_url: "/progress",
        viewed_url: "/viewed", guid: "guid-1", binge_mode: true, next_url: "/next", ...configPatch,
    }) };
    const requests = [];
    const intervals = new Map();
    let nextInterval = 1;
    const navigations = [];
    const documentListeners = {};
    const windowListeners = {};
    const castSession = { request: null, mediaSession: configPatch.currentCastMedia ? { media: { contentId: configPatch.currentCastMedia } } : null,
        loadCalls: 0, getMediaSession() { return this.mediaSession; },
        loadMedia(request) { this.loadCalls += 1; this.request = request; return configPatch.castLoadDeferred?.promise || (configPatch.castLoadFailure ? Promise.reject(new Error("failed")) : Promise.resolve()); } };
    const castContext = {
        sessionListener: null,
        setOptions(options) { this.options = options; this.setOptionsCalls = (this.setOptionsCalls || 0) + 1; },
        addEventListener(_type, listener) { this.sessionListener = listener; },
        getCurrentSession() { return castSession; },
    };
    const castApi = {
        context: castContext, session: castSession,
        framework: { CastContext: { getInstance: () => castContext },
            CastContextEventType: { SESSION_STATE_CHANGED: "session-state" },
            SessionState: { SESSION_STARTING: "SESSION_STARTING", SESSION_STARTED: "SESSION_STARTED", SESSION_RESUMING: "SESSION_RESUMING", SESSION_RESUMED: "SESSION_RESUMED", SESSION_ENDING: "SESSION_ENDING", SESSION_ENDED: "SESSION_ENDED" } },
    };
    const chromeApi = { cast: { AutoJoinPolicy: { ORIGIN_SCOPED: "ORIGIN_SCOPED" },
        media: { DEFAULT_MEDIA_RECEIVER_APP_ID: "CC1AD845", TrackType: { TEXT: "TEXT" }, TextTrackType: { SUBTITLES: "SUBTITLES" },
            Track: class { constructor(trackId, trackType) { this.trackId = trackId; this.trackType = trackType; } },
            MediaInfo: class { constructor(contentId, contentType) { this.contentId = contentId; this.contentType = contentType; } },
            LoadRequest: class { constructor(mediaInfo) { this.media = mediaInfo; } } } } };
    const window = { addEventListener(type, fn) { windowListeners[type] = fn; }, location: { assign(url) { navigations.push(url); } } };
    window.__mockProvideCast = () => { window.cast = castApi; window.chrome = chromeApi; };
    const context = {
        document: {
            cookie: "", visibilityState: "visible",
            head: { append(script) { this.script = script; this.callbackAtAppend = window.__onGCastApiAvailable; if (!configPatch.castApiLate) queueMicrotask(() => { if (!configPatch.castUnavailable) window.__mockProvideCast(); window.__onGCastApiAvailable?.(!configPatch.castUnavailable); if (configPatch.castNoDevices) elements["cast-video"].style.display = "none"; }); } },
            getElementById(id) { return id === "retry-video" ? retryButton : elements[id] || null; },
            createElement(tag) { return { tagName: tag }; },
            addEventListener(type, fn) { documentListeners[type] = fn; },
        },
        window,
        fetch: (url, options = {}) => { requests.push({ url, options }); return url === "/media" && !configPatch.testMediaFetch ? Promise.resolve(media(configPatch.testMediaResponse)) : fetcher(url, options, requests.length - 1); },
        URLSearchParams,
        setInterval(fn) { const id = nextInterval++; intervals.set(id, fn); return id; },
        clearInterval(id) { intervals.delete(id); },
    };
    vm.runInNewContext(source, context);
    return { elements, video, requests, intervals, navigations, documentListeners, windowListeners, context };
}

const ok = (body = {}) => ({ ok: true, json: async () => body });
const media = (body = {}) => ok({ source_url: "https://bucket.example/video.mp4", subtitle_urls: [], ...body });
const requestBody = (request) => Object.fromEntries(new URLSearchParams(request.options.body || ""));

test("loading status has a reduced-motion-aware CSS animation", () => {
    assert.match(styles, /\.b2-player-status\[data-loading\s*=\s*"true"\]/);
    assert.match(styles, /@media\s*\(prefers-reduced-motion:\s*no-preference\)/);
    assert.match(styles, /\.b2-loading-letter[\s\S]*?--i/);
    assert.match(styles, /\.b2-player-status\[data-loading\s*=\s*"true"\] \.b2-loading-letter[\s\S]*?animation: loading-hop/);
    assert.doesNotMatch(styles, /loading-progress|\.b2-loading-text::after/);
    assert.doesNotMatch(styles, /loading-scroll|text-indent/);
    assert.match(styles, /\.b2-resume-notice\s*\{\s*animation:\s*resume-notice-fade 20\.5s/);
    assert.match(styles, /@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*?resume-notice-dismiss 20s steps\(1, end\)/);
});

test("Cast launcher is SDK-managed, hidden before initialization, and sized as a usable control", () => {
    assert.match(template, /<google-cast-launcher[^>]*id="cast-video"[^>]*hidden/);
    assert.match(styles, /google-cast-launcher\s*\{[^}]*width:\s*2\.75rem[^}]*height:\s*2\.5rem/);
});

test("saved-position notice is isolated for timed dismissal and replacement", async () => {
    const player = createPlayer(async (url, options) => url === "/progress" && options.method === "GET" ? ok({ offset: 30 }) : ok());
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const status = player.elements["player-status"];
    assert.equal(status.textContent, "Position loaded");
    assert.match(status._html, /class="b2-resume-notice"/);

    player.video.dispatch("error");
    assert.doesNotMatch(status._html, /b2-resume-notice/);
    player.context.document.getElementById("retry-video").click();
    assert.equal(status.textContent, "Retrying…");
    assert.doesNotMatch(status._html, /b2-resume-notice/);
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.equal(status.textContent, "Position loaded");
    assert.match(status._html, /class="b2-resume-notice"/);
});

test("failed saved-position lookup does not create a fading notice", async () => {
    const player = createPlayer(async (url, options) => url === "/progress" && options.method === "GET" ? Promise.reject(new Error("offline")) : ok());
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const status = player.elements["player-status"];
    assert.equal(status.textContent, "Position could not be loaded");
    assert.doesNotMatch(status._html, /b2-resume-notice/);
});

test("failed playback-position save shows a fading notice", async () => {
    const player = createPlayer(async (_url, options) => options.method === "POST" ? { ok: false } : ok({ offset: null }));
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 10;
    player.video.dispatch("pause");
    await tick();
    const status = player.elements["player-status"];
    assert.equal(status.textContent, "Could not save playback position");
    assert.match(status._html, /class="b2-resume-notice"/);
});

test("loading animation follows media fetch, metadata, failure, and retry lifecycle", async () => {
    const pending = deferred();
    let mediaCalls = 0;
    const player = createPlayer((url) => {
        if (url !== "/media") return Promise.resolve(ok());
        mediaCalls += 1;
        return mediaCalls === 1 ? pending.promise : Promise.resolve(media());
    }, { testMediaFetch: true });
    const status = player.elements["player-status"];
    assert.equal(status.attributes["data-loading"], "true");
    await tick();
    assert.equal(status.attributes["data-loading"], "true");
    const loadingMarkup = status._html;
    const visualLetters = [...loadingMarkup.matchAll(/class="b2-loading-letter"[^>]*>(.*?)<\/span>/g)].map((match) => match[1]).join("");
    assert.equal(visualLetters, "Loading video…");
    assert.match(loadingMarkup, /aria-hidden="true"/);
    assert.match(loadingMarkup, /class="visually-hidden">Loading video…<\/span>/);
    pending.resolve(media());
    await tick();
    player.video.dispatch("loadedmetadata");
    assert.equal(status.attributes["data-loading"], undefined);

    player.video.dispatch("error");
    assert.equal(status.attributes["data-loading"], undefined);
    player.context.document.getElementById("retry-video").click();
    assert.equal(status.attributes["data-loading"], "true");
    await tick();
    player.video.dispatch("loadedmetadata");
    assert.equal(status.attributes["data-loading"], undefined);
});

test("media fetch failure stops loading animation", async () => {
    const player = createPlayer((url) => url === "/media" ? Promise.resolve({ ok: false }) : Promise.resolve(ok()), { testMediaFetch: true });
    await tick();
    assert.equal(player.elements["player-status"].attributes["data-loading"], undefined);
});

test("binge button color follows initial state and each toggle", () => {
    for (const initial of [true, false]) {
        const player = createPlayer(async () => ok(), { binge_mode: initial });
        const button = player.elements["binge-toggle"];
        const assertState = (enabled) => {
            assert.equal(button.classes.has("btn-success"), enabled);
            assert.equal(button.classes.has("btn-danger"), !enabled);
            assert.equal(button.textContent, `Binge mode: ${enabled ? "On" : "Off"}`);
            assert.equal(button.attributes["aria-pressed"], String(enabled));
        };
        assertState(initial);
        button.click();
        assertState(!initial);
        button.click();
        assertState(initial);
    }
});

test("zero offset is ready; completion at 95% does not navigate; ended obeys binge toggle", async () => {
    const player = createPlayer(async (url, options) => url === "/progress" && options.method === "GET" ? ok({ offset: 0 }) : ok());
    await tick();
    player.video.readyState = 1;
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.equal(player.video.currentTime, 0);
    assert.match(player.elements["player-status"].textContent, /Ready to play/);
    assert.match(player.elements["player-status"]._html, /class="b2-resume-notice"/);
    player.video.currentTime = 95;
    player.video.dispatch("timeupdate");
    await tick();
    assert.deepEqual(player.navigations, []);
    player.elements["binge-toggle"].click();
    player.video.dispatch("ended");
    await tick();
    assert.deepEqual(player.navigations, []);
    player.elements["binge-toggle"].click();
    player.video.dispatch("ended");
    await tick();
    assert.deepEqual(player.navigations, ["/next"]);
});

test("pause and play at 96% continues without recreating progress", async () => {
    const player = createPlayer(async () => ok());
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 95;
    player.video.dispatch("timeupdate");
    await tick();
    player.video.currentTime = 96;
    player.video.dispatch("pause");
    player.video.dispatch("play");
    await tick();
    assert.equal(player.video.paused, false);
    assert.equal(player.requests.filter((request) => request.url === "/progress" && request.options.method === "POST").length, 0);
});

test("native replay from the beginning resets completion and starts one save timer", async () => {
    const player = createPlayer(async () => ok());
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 95;
    player.video.dispatch("timeupdate");
    await tick();
    player.video.dispatch("ended");
    await tick();
    player.video.currentTime = 0;
    player.video.dispatch("play");
    assert.equal(player.video.paused, false);
    assert.equal(player.intervals.size, 1);
    [...player.intervals.values()][0]();
    await tick();
    assert.equal(player.intervals.size, 1);
    assert.equal(player.requests.filter((request) => request.url === "/progress" && request.options.method === "POST").length, 1);
});

test("Start Over invalidates an unresolved initial GET and leaves position at zero", async () => {
    const get = deferred();
    const player = createPlayer((url, options) => options.method === "GET" ? get.promise : Promise.resolve(ok()));
    await tick();
    player.video.dispatch("loadedmetadata");
    const restart = player.elements["start-over"].click();
    await tick();
    get.resolve(ok({ offset: 80 }));
    await tick();
    await restart;
    assert.equal(player.video.currentTime, 0);
    assert.doesNotMatch(player.elements["player-status"].textContent, /Resume position ready/);
    assert.doesNotMatch(player.elements["player-status"]._html, /b2-resume-notice/);
});

test("pending old save is skipped at restart; threshold and subsequent play save normally", async () => {
    const post = deferred();
    let held = false;
    const player = createPlayer((url, options) => {
        if (options.method === "GET") return Promise.resolve(ok({ offset: 0 }));
        if (options.method === "POST" && !held) { held = true; return post.promise; }
        return Promise.resolve(ok());
    });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 94.9;
    player.video.dispatch("pause");
    const restart = player.elements["start-over"].click();
    player.video.currentTime = 95;
    player.video.dispatch("timeupdate");
    post.resolve(ok());
    await restart;
    await tick();
    assert.equal(player.requests.filter((r) => r.url === "/viewed").length, 0);
    assert.equal(player.video.currentTime, 0);
    player.video.paused = false;
    player.video.dispatch("play");
    assert.equal(player.intervals.size, 1);
    player.video.pause();
    player.video.paused = false;
    player.video.dispatch("play");
    assert.equal(player.intervals.size, 1, "native replay does not duplicate timer");
    [...player.intervals.values()][0]();
    await tick();
    assert(player.requests.some((r) => r.options.method === "POST" && requestBody(r).offset === "0"));
});

test("old completion is invalidated by restart and cannot mark viewed or overwrite status", async () => {
    const deletion = deferred();
    const player = createPlayer((url, options) => options.method === "DELETE" ? deletion.promise : Promise.resolve(ok()));
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 95;
    player.video.dispatch("timeupdate");
    await tick();
    const restart = player.elements["start-over"].click();
    deletion.resolve(ok());
    await restart;
    await tick();
    assert.equal(player.requests.filter((r) => r.url === "/viewed").length, 0);
    assert.match(player.elements["player-status"].textContent, /Starting from the beginning/);
});

test("tracking failures are handled; ended navigation is consistent and no rejection escapes", async () => {
    const unhandled = [];
    const listener = (error) => unhandled.push(error);
    process.on("unhandledRejection", listener);
    const player = createPlayer(async (url, options) => ({
        ok: !(options.method === "DELETE" || url === "/viewed"), json: async () => ({ offset: null }),
    }));
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 95;
    player.video.dispatch("timeupdate");
    player.video.dispatch("timeupdate");
    await tick();
    player.video.dispatch("ended");
    await tick();
    await new Promise((resolve) => setImmediate(resolve));
    process.off("unhandledRejection", listener);
    assert.deepEqual(unhandled, []);
    assert.deepEqual(player.navigations, ["/next"]);
    assert.match(player.elements["player-status"].textContent, /could not be updated/);
});

test("retry before and after metadata reloads with selected position; stale GET is ignored", async () => {
    const firstGet = deferred();
    const player = createPlayer((url, options) => options.method === "GET" ? firstGet.promise : Promise.resolve(ok()));
    await tick();
    player.video.dispatch("loadedmetadata");
    player.video.dispatch("error");
    player.context.document.getElementById("retry-video").click();
    player.video.readyState = 0;
    player.video.currentTime = 0;
    player.video.dispatch("loadedmetadata");
    await tick();
    firstGet.resolve(ok({ offset: 80 }));
    await tick();
    assert.notEqual(player.video.currentTime, 80);

    player.video.dispatch("error");
    player.video.currentTime = 23;
    player.video.dispatch("error");
    player.context.document.getElementById("retry-video").click();
    assert.equal(player.video.currentTime, 23);
    assert.equal(player.elements["player-status"].textContent, "Retrying…");
    const retryMarkup = player.elements["player-status"]._html;
    assert.match(retryMarkup, /class="b2-loading-letter"/);
    assert.match(retryMarkup, /class="visually-hidden">Retrying…<\/span>/);
});

test("page exit serializes a keepalive save behind pending writes", async () => {
    const pending = deferred();
    const player = createPlayer((url, options) => options.method === "GET" ? Promise.resolve(ok({ offset: null })) : options.method === "POST" ? pending.promise : Promise.resolve(ok()));
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 31;
    player.video.dispatch("pause");
    await tick();
    player.context.document.visibilityState = "hidden";
    player.documentListeners.visibilitychange();
    assert.equal(player.requests.filter((r) => r.options.method === "POST").length, 1);
    pending.resolve(ok());
    await tick();
    const exitSave = player.requests.filter((r) => r.options.method === "POST")[1];
    assert(exitSave);
    assert.equal(exitSave.options.keepalive, true);
});

test("failed Start Over clear remains visible and playback can continue", async () => {
    const player = createPlayer(async (_url, options) => options.method === "DELETE" ? { ok: false } : ok());
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const restart = player.elements["start-over"].click();
    await restart;
    assert.match(player.elements["player-status"].textContent, /Could not clear/);
    assert.equal(player.video.currentTime, 0);
    player.video.paused = false;
    player.video.dispatch("play");
    assert.equal(player.intervals.size, 1);
});

test("media URL fetch defers source attachment and load until success", async () => {
    const pending = deferred();
    const player = createPlayer((url) => url === "/media" ? pending.promise : Promise.resolve(ok()), { testMediaFetch: true });
    assert.equal(player.video.children.length, 0);
    assert.equal(player.video.loadCalls, 0);
    assert.match(player.elements["player-status"].textContent, /Loading video/);
    pending.resolve(media());
    await tick();
    assert.equal(player.video.children.filter((child) => child.tagName === "source").length, 1);
    assert.equal(player.video.loadCalls, 1);
});

test("initial media load starts immediately without scheduling a timeout", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true });
    assert.equal(player.elements["player-status"].attributes["data-loading"], "true");
    await tick();
    assert.equal(player.requests.filter((request) => request.url === "/media").length, 1);
    assert.equal(player.video.children.filter((child) => child.tagName === "source").length, 1);
    assert.equal(player.video.loadCalls, 1);
});

test("AirPlay option appears on availability before playback and opens picker on click", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, airplaySupported: true });
    const button = player.elements["airplay-video"];
    assert.equal(button.hidden, true);
    await tick();
    player.video.dispatch("loadedmetadata");
    assert.equal(player.video.paused, true);
    player.video.dispatch("webkitplaybacktargetavailabilitychanged", { availability: "available" });
    assert.equal(button.hidden, false);
    button.click();
    assert.equal(player.video.pickerCalls, 1);
    player.video.dispatch("webkitplaybacktargetavailabilitychanged", { availability: "not-available" });
    assert.equal(button.hidden, true);
});

test("AirPlay option stays hidden when native picker is unsupported", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true });
    await tick();
    player.video.dispatch("loadedmetadata");
    assert.equal(player.elements["airplay-video"].hidden, true);
});

test("Cast SDK initializes receiver before playback and loads the signed source after session start", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true });
    const script = player.context.document.head.script;
    assert.equal(typeof player.context.document.head.callbackAtAppend, "function");
    assert.equal(script.src, "https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1");
    assert.equal(player.elements["cast-video"].hidden, true);
    await tick();
    const cast = player.context.window.cast;
    assert.equal(cast.context.setOptionsCalls, 1);
    assert.equal(cast.context.options.receiverApplicationId, "CC1AD845");
    assert.equal(player.elements["cast-video"].hidden, false);
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.currentTime = 24;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    assert.equal(cast.session.request.media.contentId, "https://bucket.example/video.mp4");
    assert.equal(cast.session.request.currentTime, 24);
    assert.equal(player.video.paused, true);
    assert.equal(player.video.controls, false);
    assert.equal(player.video.playCalls || 0, 0);
    cast.context.sessionListener({ sessionState: "SESSION_ENDED" });
    assert.equal(player.video.controls, true);
});

test("Cast load includes signed subtitle tracks and activates first track when captions are enabled", async () => {
    const urls = ["https://bucket.example/en.vtt?signature=one", "https://bucket.example/en-alt.vtt?signature=two"];
    const player = createPlayer(async () => media({ subtitle_urls: urls }), { testMediaFetch: true, captions_enabled: true });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    const { media: castMedia, activeTrackIds } = cast.session.request;
    assert.deepEqual(castMedia.tracks.map((track) => ({
        trackId: track.trackId, trackType: track.trackType, trackContentId: track.trackContentId,
        trackContentType: track.trackContentType, subtype: track.subtype, language: track.language, name: track.name,
    })), [
        { trackId: 1, trackType: "TEXT", trackContentId: urls[0], trackContentType: "text/vtt", subtype: "SUBTITLES", language: "en", name: "English" },
        { trackId: 2, trackType: "TEXT", trackContentId: urls[1], trackContentType: "text/vtt", subtype: "SUBTITLES", language: "en", name: "English 2" },
    ]);
    assert.deepEqual(Array.from(activeTrackIds), [1]);
});

test("Cast includes selectable subtitle tracks but activates none when captions are disabled", async () => {
    const player = createPlayer(async () => media({ subtitle_urls: ["https://bucket.example/en.vtt"] }), { testMediaFetch: true, captions_enabled: false });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    assert.equal(cast.session.request.media.tracks.length, 1);
    assert.deepEqual(Array.from(cast.session.request.activeTrackIds), []);
});

test("Cast safely loads without subtitle tracks", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, captions_enabled: true });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    assert.deepEqual(Array.from(cast.session.request.media.tracks), []);
    assert.deepEqual(Array.from(cast.session.request.activeTrackIds), []);
});

test("Cast honors local caption preference toggled before casting", async () => {
    const player = createPlayer(async () => media({ subtitle_urls: ["https://bucket.example/en.vtt"] }), { testMediaFetch: true, captions_enabled: false });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.textTracks.tracks[0].mode = "showing";
    dispatchTrackChange(player);
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    assert.deepEqual(Array.from(cast.session.request.activeTrackIds), [1]);
});

test("Cast resume reuses matching media and ignores other media and intermediate states", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, currentCastMedia: "https://bucket.example/video.mp4" });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const { session, context: castContext } = player.context.window.cast;
    castContext.sessionListener({ sessionState: "SESSION_RESUMING" });
    assert.equal(player.elements["player-status"].textContent, "Ready to play");
    castContext.sessionListener({ sessionState: "SESSION_RESUMED" });
    assert.equal(session.loadCalls, 0);
    assert.equal(player.video.controls, false);
    castContext.sessionListener({ sessionState: "SESSION_ENDED" });
    assert.equal(player.elements["player-status"].textContent, "Casting ended. Press play to continue here.");

    const other = createPlayer(async () => media(), { testMediaFetch: true, currentCastMedia: "https://other.example/movie.mp4" });
    await tick();
    const otherCast = other.context.window.cast;
    otherCast.context.sessionListener({ sessionState: "SESSION_RESUMED" });
    assert.equal(otherCast.session.loadCalls, 0);
    assert.equal(other.video.controls, true);
});

test("Cast waits for saved resume position before loading and ignores stale callbacks after disconnect", async () => {
    const progress = deferred();
    const load = deferred();
    const player = createPlayer((url, options) => url === "/media" ? Promise.resolve(media()) : url === "/progress" && options.method === "GET" ? progress.promise : Promise.resolve(ok()), {
        testMediaFetch: true, castLoadDeferred: load,
    });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    assert.equal(cast.session.loadCalls, 0);
    progress.resolve(ok({ offset: 30 }));
    await tick();
    assert.equal(cast.session.loadCalls, 1);
    assert.equal(cast.session.request.currentTime, 30);
    assert.equal(player.elements["player-status"].textContent, "Connecting to Chromecast");
    cast.context.sessionListener({ sessionState: "SESSION_ENDED" });
    load.resolve();
    await tick();
    assert.equal(player.video.controls, true);
    assert.equal(player.elements["player-status"].textContent, "Casting ended. Press play to continue here.");
});

test("Cast loads from zero when saved-position lookup fails", async () => {
    const player = createPlayer((url, options) => url === "/media" ? Promise.resolve(media()) : url === "/progress" && options.method === "GET" ? Promise.reject(new Error("offline")) : Promise.resolve(ok()), { testMediaFetch: true });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    assert.equal(cast.session.loadCalls, 1);
    assert.equal(cast.session.request.currentTime, 0);
});

test("Cast active state gates local playback and tools; duplicate session events do not reload", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    assert.equal(cast.session.loadCalls, 1);
    assert.equal(player.elements["seek-back"].disabled, true);
    player.video.dispatch("play");
    assert.equal(player.video.paused, true);
    cast.context.sessionListener({ sessionState: "SESSION_ENDED" });
    assert.equal(player.elements["seek-back"].disabled, false);
});

test("Cast session waits for media source and loads it once when ready", async () => {
    const pending = deferred();
    const player = createPlayer((url) => url === "/media" ? pending.promise : Promise.resolve(ok()), { testMediaFetch: true });
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    assert.equal(cast.session.request, null);
    pending.resolve(media());
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.equal(cast.session.request.media.contentId, "https://bucket.example/video.mp4");
    assert.equal(cast.session.request.currentTime, 0);
});

test("Cast media failure restores local controls without exposing SDK errors", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, castLoadFailure: true });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const cast = player.context.window.cast;
    cast.context.sessionListener({ sessionState: "SESSION_STARTED" });
    await tick();
    assert.equal(player.video.controls, true);
    assert.match(player.elements["player-status"].textContent, /Could not start casting/);
    assert.doesNotMatch(player.elements["player-status"].textContent, /failed/);
});

test("Cast SDK becoming available after media load remains supported", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, castApiLate: true });
    await tick();
    assert.equal(typeof player.context.window.__onGCastApiAvailable, "function");
    player.context.window.__mockProvideCast();
    player.context.window.__onGCastApiAvailable(true);
    assert.equal(player.context.window.cast.context.setOptionsCalls, 1);
    player.context.window.__onGCastApiAvailable(true);
    assert.equal(player.context.window.cast.context.setOptionsCalls, 1);
});

test("unavailable Cast SDK leaves launcher hidden and local playback usable", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, castUnavailable: true });
    await tick();
    assert.equal(player.elements["cast-video"].hidden, true);
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.dispatch("play");
    assert.equal(player.video.paused, false);
});

test("Cast launcher visibility remains under SDK control when no receivers are available", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, castNoDevices: true });
    await tick();
    assert.equal(typeof player.context.document.head.callbackAtAppend, "function");
    assert.equal(player.elements["cast-video"].style.display, "none");
});

test("Cast initialization failure leaves local player usable", async () => {
    const player = createPlayer(async () => media(), { testMediaFetch: true, castApiLate: true });
    await tick();
    player.context.window.__mockProvideCast();
    player.context.window.__onGCastApiAvailable(false);
    player.video.dispatch("loadedmetadata");
    await tick();
    player.video.dispatch("play");
    assert.equal(player.video.paused, false);
    assert.equal(player.elements["player-status"].textContent, "");
});

test("media URL failures show safe retry and retry without duplicate source or tracks", async () => {
    let count = 0;
    const player = createPlayer((url) => url === "/media" ? Promise.resolve(++count === 1 ? { ok: false, status: 502 } : ok({ source_url: "https://bucket.example/video.mp4", subtitle_urls: ["https://bucket.example/en.vtt"] })) : Promise.resolve(ok()), { testMediaFetch: true });
    await tick();
    assert.match(player.elements["player-status"]._html, /could not be loaded/i);
    player.context.document.getElementById("retry-video").click();
    await tick();
    assert.equal(player.video.children.filter((child) => child.tagName === "source").length, 1);
    assert.equal(player.video.children.filter((child) => child.tagName === "track").length, 1);
    assert.equal(player.video.loadCalls, 1);
});

test("network and malformed media responses fail without exposing response details", async () => {
    for (const fetcher of [() => Promise.reject(new Error("secret signed URL")), () => Promise.resolve(ok({ source_url: "" }))]) {
        const player = createPlayer((url) => url === "/media" ? fetcher() : Promise.resolve(ok()), { testMediaFetch: true });
        await tick();
        assert.match(player.elements["player-status"]._html, /could not be loaded/i);
        assert.doesNotMatch(player.elements["player-status"]._html, /secret|bucket\.example/);
        assert.equal(player.video.children.length, 0);
        assert.equal(player.video.loadCalls, 0);
    }
});

test("double retry clicks during a pending media request do not duplicate requests", async () => {
    const pending = deferred();
    let mediaCalls = 0;
    const player = createPlayer((url) => {
        if (url !== "/media") return Promise.resolve(ok());
        mediaCalls += 1;
        return mediaCalls === 1 ? Promise.resolve({ ok: false }) : pending.promise;
    }, { testMediaFetch: true });
    await tick();
    player.context.document.getElementById("retry-video").click();
    await tick();
    player.context.document.getElementById("retry-video").click();
    assert.equal(mediaCalls, 2);
    pending.resolve(media());
    await tick();
    assert.equal(player.video.children.filter((child) => child.tagName === "source").length, 1);
});

test("malformed JSON shows safe retry without attaching media", async () => {
    const player = createPlayer((url) => url === "/media"
        ? Promise.resolve({ ok: true, json: async () => { throw new Error("private response data"); } })
        : Promise.resolve(ok()), { testMediaFetch: true });
    await tick();
    assert.match(player.elements["player-status"]._html, /could not be loaded/i);
    assert.doesNotMatch(player.elements["player-status"]._html, /private response data/);
    assert.equal(player.video.children.length, 0);
    assert.equal(player.video.loadCalls, 0);
});

test("media error retry preserves playback position and does not duplicate subtitle tracks", async () => {
    const player = createPlayer((url) => url === "/media"
        ? Promise.resolve(ok({
            source_url: "https://bucket.example/video.mp4",
            subtitle_urls: ["https://bucket.example/en.vtt", "https://bucket.example/fr.vtt"],
        }))
        : Promise.resolve(ok()), { testMediaFetch: true });
    await tick();
    player.video.currentTime = 42;
    player.video.dispatch("error");
    player.context.document.getElementById("retry-video").click();
    assert.equal(player.video.currentTime, 42);
    assert.equal(player.video.children.filter((child) => child.tagName === "source").length, 1);
    assert.equal(player.video.children.filter((child) => child.tagName === "track").length, 2);
});

const captionTracks = (player) => player.video.textTracks.tracks;
const captionPosts = (player) => player.requests.filter((request) => request.url === "/captions" && request.options.method === "POST");
const dispatchTrackChange = (player) => player.video.textTracks.dispatch("change");

test("saved captions-on preference initializes first subtitle without posting", async () => {
    const player = createPlayer((url, options) => options.method === "GET" ? Promise.resolve(ok({ offset: null })) : Promise.resolve(ok()), {
        testMediaResponse: { subtitle_urls: ["/en.vtt", "/fr.vtt"] }, captions_url: "/captions", captions_enabled: true,
    });
    await tick();
    assert.equal(captionTracks(player).length, 2);
    assert.equal(player.video.children.filter((child) => child.tagName === "track")[0].default, true);
    assert.equal(captionTracks(player)[0].mode, "showing");
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.deepEqual(captionTracks(player).map((track) => track.mode), ["showing", "disabled"]);
    dispatchTrackChange(player);
    await tick();
    assert.equal(captionPosts(player).length, 0);
});

test("missing captions preference defaults off without posting initialization", async () => {
    const player = createPlayer((url, options) => options.method === "GET" ? Promise.resolve(ok({ offset: null })) : Promise.resolve(ok()), {
        testMediaResponse: { subtitle_urls: ["/en.vtt", "/fr.vtt"] }, captions_url: "/captions",
    });
    await tick();
    assert.equal(player.video.children.filter((child) => child.tagName === "track")[0].default, false);
    assert.deepEqual(captionTracks(player).map((track) => track.mode), ["disabled", "disabled"]);
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.deepEqual(captionTracks(player).map((track) => track.mode), ["disabled", "disabled"]);
    assert.equal(captionPosts(player).length, 0);
});

test("saved captions-off preference initializes every subtitle disabled without posting", async () => {
    const player = createPlayer((url, options) => options.method === "GET" ? Promise.resolve(ok({ offset: null })) : Promise.resolve(ok()), {
        testMediaResponse: { subtitle_urls: ["/en.vtt", "/fr.vtt"] }, captions_url: "/captions", captions_enabled: false,
    });
    await tick();
    assert.equal(player.video.children.filter((child) => child.tagName === "track")[0].default, false);
    assert.deepEqual(captionTracks(player).map((track) => track.mode), ["disabled", "disabled"]);
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.deepEqual(captionTracks(player).map((track) => track.mode), ["disabled", "disabled"]);
    assert.equal(captionPosts(player).length, 0);
});

test("caption menu transitions persist on and off, ignoring language and duplicate changes", async () => {
    const player = createPlayer((url, options) => url === "/progress" && options.method === "GET" ? Promise.resolve(ok({ offset: null })) : Promise.resolve(ok()), {
        testMediaResponse: { subtitle_urls: ["/en.vtt", "/fr.vtt"] }, captions_url: "/captions", captions_enabled: true,
    });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const [english, french] = captionTracks(player);
    french.mode = "showing";
    dispatchTrackChange(player);
    english.mode = "disabled";
    dispatchTrackChange(player);
    await tick();
    assert.equal(captionPosts(player).length, 0, "switching languages while captions stay enabled is not a preference change");
    french.mode = "disabled";
    dispatchTrackChange(player);
    dispatchTrackChange(player);
    english.mode = "showing";
    dispatchTrackChange(player);
    french.mode = "showing";
    dispatchTrackChange(player);
    await tick();
    assert.deepEqual(captionPosts(player).map(requestBody), [
        { captions_enabled: "false" }, { captions_enabled: "true" },
    ]);
});

test("no-subtitle media and failed caption saves do not affect playback", async () => {
    const player = createPlayer((url, options) => url === "/media"
        ? Promise.resolve(ok({ source_url: "https://bucket.example/video.mp4", subtitle_urls: [] }))
        : url === "/captions" ? Promise.resolve({ ok: false }) : Promise.resolve(ok({ offset: null })), {
        captions_url: "/captions", captions_enabled: true,
    });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.equal(player.video.textTracks.length, 0);
    assert.equal(captionPosts(player).length, 0);
    player.video.textTracks.add({ kind: "metadata", mode: "disabled" });
    dispatchTrackChange(player);
    await tick();
    assert.equal(captionPosts(player).length, 0, "unrelated tracks are ignored");
    player.video.textTracks.tracks[0].mode = "showing";
    dispatchTrackChange(player);
    await tick();
    assert.equal(captionPosts(player).length, 0);
    player.video.textTracks.add({ kind: "subtitles", mode: "disabled" });
    dispatchTrackChange(player);
    await tick();
    player.video.dispatch("play");
    assert.equal(player.video.paused, false);
    assert.equal(captionPosts(player).length, 1);
});

test("rapid caption choices are serialized and retry restores latest local preference", async () => {
    const firstPost = deferred();
    let heldCaptionPost = false;
    const player = createPlayer((url, options) => url === "/progress" && options.method === "GET"
        ? Promise.resolve(ok({ offset: null }))
        : url === "/captions" && !heldCaptionPost ? (heldCaptionPost = true, firstPost.promise) : Promise.resolve(ok()), {
        testMediaResponse: { subtitle_urls: ["/en.vtt", "/fr.vtt"] }, captions_url: "/captions", captions_enabled: true,
    });
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    const [english] = captionTracks(player);
    english.mode = "disabled";
    dispatchTrackChange(player);
    await tick();
    english.mode = "showing";
    dispatchTrackChange(player);
    await tick();
    assert.deepEqual(captionPosts(player).map(requestBody), [{ captions_enabled: "false" }]);
    firstPost.resolve(ok());
    await tick();
    assert.deepEqual(captionPosts(player).map(requestBody), [{ captions_enabled: "false" }, { captions_enabled: "true" }]);
    english.mode = "disabled";
    dispatchTrackChange(player);
    await tick();
    assert.deepEqual(captionPosts(player).map(requestBody), [
        { captions_enabled: "false" }, { captions_enabled: "true" }, { captions_enabled: "false" },
    ]);
    player.video.dispatch("error");
    player.context.document.getElementById("retry-video").click();
    await tick();
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.deepEqual(captionTracks(player).map((track) => track.mode), ["disabled", "disabled"]);
    dispatchTrackChange(player);
    await tick();
    assert.equal(captionPosts(player).length, 3, "retry initialization does not overwrite or repost preference");
});
