const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "../../static/assets/b2player.js"), "utf8");
const tick = async () => { for (let index = 0; index < 12; index += 1) await Promise.resolve(); };
const deferred = () => {
    let resolve;
    let reject;
    const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
    return { promise, resolve, reject };
};

function createPlayer(fetcher = async () => ({ ok: true, json: async () => ({ offset: null }) }), configPatch = {}) {
    const ids = ["player-status", "seek-back", "seek-forward", "start-over", "binge-toggle"];
    const elements = Object.fromEntries(ids.map((id) => [id, {
        id, textContent: "", attributes: {}, listeners: {},
        addEventListener(type, fn) { this.listeners[type] = fn; },
        setAttribute(name, value) { this.attributes[name] = value; },
        click() { return this.listeners.click?.(); },
    }]));
    const listeners = new Map();
    const retryButton = { listeners: {}, addEventListener(type, fn) { this.listeners[type] = fn; }, click() { return this.listeners.click?.(); } };
    Object.defineProperty(elements["player-status"], "innerHTML", {
        set(value) { this._html = value; }, get() { return this._html; },
    });
    const video = {
        currentTime: 0, duration: 100, paused: true, readyState: 0, children: [], loadCalls: 0,
        append(child) { child.remove = () => { this.children = this.children.filter((item) => item !== child); }; this.children.push(child); },
        querySelector(tag) { return this.children.find((child) => child.tagName === tag); },
        querySelectorAll(selector) { return this.children.filter((child) => selector.split(", ").includes(child.tagName)); },
        addEventListener(type, fn, options = {}) { const entries = listeners.get(type) || []; entries.push({ fn, once: options.once }); listeners.set(type, entries); },
        dispatch(type) {
            if (type === "play") this.paused = false;
            if (type === "pause" || type === "ended") this.paused = true;
            if (type === "ended") this.currentTime = this.duration;
            const entries = listeners.get(type) || [];
            for (const entry of [...entries]) {
                entry.fn();
                if (entry.once) entries.splice(entries.indexOf(entry), 1);
            }
        },
        pause() { this.paused = true; this.dispatch("pause"); },
        load() { this.loadCalls += 1; },
    };
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
    const context = {
        document: {
            cookie: "", visibilityState: "visible",
            getElementById(id) { return id === "retry-video" ? retryButton : elements[id] || null; },
            createElement(tag) { return { tagName: tag }; },
            addEventListener(type, fn) { documentListeners[type] = fn; },
        },
        window: { addEventListener(type, fn) { windowListeners[type] = fn; }, location: { assign(url) { navigations.push(url); } } },
        fetch: (url, options = {}) => { requests.push({ url, options }); return url === "/media" && !configPatch.testMediaFetch ? Promise.resolve(media()) : fetcher(url, options, requests.length - 1); },
        URLSearchParams,
        setInterval(fn) { const id = nextInterval++; intervals.set(id, fn); return id; },
        clearInterval(id) { intervals.delete(id); },
    };
    vm.runInNewContext(source, context);
    return { elements, video, requests, intervals, navigations, documentListeners, windowListeners, context };
}

const ok = (body = {}) => ({ ok: true, json: async () => body });
const media = () => ok({ source_url: "https://bucket.example/video.mp4", subtitle_urls: [] });
const requestBody = (request) => Object.fromEntries(new URLSearchParams(request.options.body || ""));

test("zero offset is ready; completion at 95% does not navigate; ended obeys binge toggle", async () => {
    const player = createPlayer(async (url, options) => url === "/progress" && options.method === "GET" ? ok({ offset: 0 }) : ok());
    await tick();
    player.video.readyState = 1;
    player.video.dispatch("loadedmetadata");
    await tick();
    assert.equal(player.video.currentTime, 0);
    assert.match(player.elements["player-status"].textContent, /Ready to play/);
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
