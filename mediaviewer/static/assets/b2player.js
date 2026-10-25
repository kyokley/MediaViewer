(() => {
  "use strict";

  const video = document.getElementById("b2-video");
  const status = document.getElementById("player-status");
  const configNode = document.getElementById("b2-player-config");
  if (!video || !status || !configNode) return;

  let config;
  try {
    config = JSON.parse(configNode.textContent);
  } catch (_) {
    status.textContent =
      "Player setup could not be read. Reload this page to try again.";
    return;
  }
  const validOffset = (value) => {
    const offset = Number(value);
    return Number.isFinite(offset) && offset >= 0 ? offset : null;
  };
  const cookie = (name) =>
    document.cookie
      .split(";")
      .map((part) => part.trim())
      .find((part) => part.startsWith(`${name}=`))
      ?.split("=")
      .slice(1)
      .join("=");
  const csrf = decodeURIComponent(cookie("csrftoken") || "");
  const request = async (url, method, values, keepalive = false) => {
    const options = {
      method,
      credentials: "same-origin",
      keepalive,
      headers: { "X-CSRFToken": csrf },
    };
    if (values) {
      options.headers["Content-Type"] =
        "application/x-www-form-urlencoded;charset=UTF-8";
      options.body = new URLSearchParams(values);
    }
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    return method === "GET" ? response.json() : null;
  };
  const progressGet = () => request(config.progress_url, "GET");
  const progressSave = (offset, keepalive = false) =>
    request(
      config.progress_url,
      "POST",
      { guid: config.guid, offset: String(offset) },
      keepalive,
    );
  const progressClear = () => request(config.progress_url, "DELETE");

  let resumeReady = false;
  let suspended = false;
  let finished = false;
  let viewedSent = false;
  let bingeEnabled = Boolean(config.binge_mode && config.next_url);
  let generation = 0;
  let loadGeneration = -1;
  let timer = null;
  let mutationQueue = Promise.resolve();
  let completionPromise = null;
  let retryOffset = 0;
  let mediaRequest = null;
  const bingeButton = document.getElementById("binge-toggle");
  const updateBingeButton = () => {
    if (!bingeButton) return;
    bingeButton.textContent = `Binge mode: ${bingeEnabled ? "On" : "Off"}`;
    bingeButton.setAttribute("aria-pressed", String(bingeEnabled));
  };
  const loadMedia = () => {
    if (mediaRequest) return mediaRequest;
    status.textContent = "Loading video…";
    mediaRequest = Promise.resolve().then(async () => {
      try {
        if (typeof config.media_url !== "string" || !config.media_url)
          throw new Error("Invalid media URL");
        const response = await fetch(config.media_url, { method: "GET", credentials: "same-origin" });
        if (!response.ok) throw new Error("Media request failed");
        const result = await response.json();
        if (!result || typeof result.source_url !== "string" || !result.source_url || !Array.isArray(result.subtitle_urls) || result.subtitle_urls.some((url) => typeof url !== "string" || !url))
          throw new Error("Invalid media response");
        video.querySelectorAll("source, track").forEach((child) => child.remove());
        const source = document.createElement("source");
        source.src = result.source_url;
        source.type = "video/mp4";
        video.append(source);
        result.subtitle_urls.forEach((url, index) => {
          const track = document.createElement("track");
          track.kind = "subtitles";
          track.srclang = "en";
          track.label = `English${index ? ` ${index + 1}` : ""}`;
          track.src = url;
          if (index === 0) track.default = true;
          video.append(track);
        });
        video.load();
      } catch (_) {
        status.innerHTML = 'Video could not be loaded. <button class="btn btn-sm btn-outline-light" id="retry-video" type="button">Retry</button>.';
        document.getElementById("retry-video")?.addEventListener("click", () => {
          if (mediaRequest) return;
          mediaRequest = null;
          loadMedia();
        });
      } finally {
        mediaRequest = null;
      }
    });
    return mediaRequest;
  };
  const setStatus = (message, ownerGeneration = generation) => {
    if (ownerGeneration === generation) status.textContent = message;
  };
  const enqueueMutation = (callback) => {
    mutationQueue = mutationQueue.catch(() => {}).then(callback);
    return mutationQueue;
  };
  const stopTimer = () => {
    if (timer !== null) clearInterval(timer);
    timer = null;
  };
  const startTimer = () => {
    if (timer === null && !finished && !suspended)
      timer = setInterval(saveProgress, 15000);
  };
  function saveProgress(keepalive = false) {
    if (
      !resumeReady ||
      suspended ||
      finished ||
      !Number.isFinite(video.currentTime)
    )
      return Promise.resolve();
    const offset = Math.max(0, video.currentTime);
    const saveGeneration = generation;
    return enqueueMutation(() =>
      saveGeneration === generation && !suspended && !finished
        ? progressSave(offset, keepalive)
        : undefined,
    ).catch(() =>
      setStatus(
        "Could not save playback position. Playback can continue.",
        saveGeneration,
      ),
    );
  }
  const complete = () => {
    if (completionPromise) return completionPromise;
    if (!Number.isFinite(video.duration) || video.duration <= 0)
      return Promise.resolve();
    const completeGeneration = generation;
    finished = true;
    stopTimer();
    completionPromise = enqueueMutation(async () => {
      if (completeGeneration !== generation) return;
      await progressClear();
      if (completeGeneration !== generation) return;
      if (!viewedSent && config.viewed_url && config.guid) {
        await request(config.viewed_url, "POST", {
          guid: config.guid,
          viewed: "True",
        });
        if (completeGeneration === generation) viewedSent = true;
      }
    })
      .then(() => {
        setStatus("Marked as viewed.", completeGeneration);
      })
      .catch(() => {
        setStatus(
          "Playback finished, but progress or viewing status could not be updated.",
          completeGeneration,
        );
      });
    return completionPromise;
  };
  const ended = async () => {
    await complete();
    if (bingeEnabled && config.next_url)
      window.location.assign(config.next_url);
  };
  const loadResume = async (expectedGeneration, offsetOnLoad = null) => {
    resumeReady = false;
    loadGeneration = expectedGeneration;
    try {
      const result =
        offsetOnLoad === null ? await progressGet() : { offset: offsetOnLoad };
      if (
        expectedGeneration !== generation ||
        loadGeneration !== expectedGeneration ||
        suspended
      )
        return;
      const offset = validOffset(result && result.offset);
      if (offset !== null && offset < video.duration && offset > 0)
        video.currentTime = offset;
      retryOffset = offset !== null && offset < video.duration ? offset : 0;
      resumeReady = true;
      setStatus(
        retryOffset > 0
          ? "Position loaded. Press play when you’re ready."
          : "Ready to play.",
        expectedGeneration,
      );
    } catch (_) {
      if (
        expectedGeneration !== generation ||
        loadGeneration !== expectedGeneration ||
        suspended
      )
        return;
      resumeReady = true;
      setStatus(
        "Position could not be loaded. Press play to start; playback will continue.",
        expectedGeneration,
      );
    }
  };

  status.textContent = "Loading video…";
  let retryPending = false;
  video.addEventListener("loadedmetadata", () => {
    if (suspended || resumeReady || loadGeneration === generation) return;
    const offset = retryPending ? retryOffset : null;
    retryPending = false;
    loadResume(generation, offset);
  });
  video.addEventListener("error", () => {
    status.innerHTML =
      'Video could not be loaded. Check that this site has access to the B2 bucket’s cross-origin resources, then <button class="btn btn-sm btn-outline-light" id="retry-video" type="button">Retry</button>.';
    document.getElementById("retry-video")?.addEventListener("click", () => {
      generation += 1;
      suspended = false;
      finished = false;
      completionPromise = null;
      stopTimer();
      retryOffset =
        Number.isFinite(video.currentTime) && video.currentTime > 0
          ? video.currentTime
          : retryOffset;
      resumeReady = false;
      retryPending = true;
      loadGeneration = -1;
      status.textContent = "Retrying…";
      video.load();
      if (video.readyState >= 1) {
        retryPending = false;
        loadResume(generation, retryOffset);
      }
    });
  });
  video.addEventListener("play", () => {
    if (
      finished &&
      video.duration > 0 &&
      video.currentTime / video.duration < 0.95
    ) {
      generation += 1;
      finished = false;
      completionPromise = null;
    }
    if (!resumeReady || suspended) {
      video.pause();
      if (!suspended) status.textContent = "Checking your saved position…";
      return;
    }
    setStatus("");
    startTimer();
  });
  video.addEventListener("pause", () => {
    saveProgress();
  });
  video.addEventListener("timeupdate", () => {
    if (
      resumeReady &&
      !suspended &&
      Number.isFinite(video.duration) &&
      video.duration > 0 &&
      video.currentTime / video.duration >= 0.95
    )
      complete();
  });
  video.addEventListener("ended", ended);
  document.getElementById("seek-back").addEventListener("click", () => {
    video.currentTime = Math.max(0, video.currentTime - 10);
  });
  document.getElementById("seek-forward").addEventListener("click", () => {
    video.currentTime = Math.min(
      video.duration || Infinity,
      video.currentTime + 10,
    );
  });
  document.getElementById("start-over").addEventListener("click", async () => {
    suspended = true;
    generation += 1;
    loadGeneration = generation;
    finished = false;
    completionPromise = null;
    retryOffset = 0;
    resumeReady = false;
    stopTimer();
    video.pause();
    const restartGeneration = generation;
    let clearFailed = false;
    try {
      await enqueueMutation(progressClear);
    } catch (_) {
      clearFailed = true;
    }
    if (restartGeneration !== generation) return;
    video.currentTime = 0;
    suspended = false;
    resumeReady = true;
    status.textContent = clearFailed
      ? "Could not clear the saved position. You can still play from the beginning."
      : "Starting from the beginning. Press play when you’re ready.";
    if (!video.paused) startTimer();
  });
  if (bingeButton) {
    updateBingeButton();
    bingeButton.addEventListener("click", () => {
      bingeEnabled = !bingeEnabled;
      updateBingeButton();
    });
  }
  const flushOnExit = () => {
    if (
      !resumeReady ||
      suspended ||
      finished ||
      !Number.isFinite(video.currentTime)
    )
      return;
    const offset = Math.max(0, video.currentTime);
    const exitGeneration = generation;
    enqueueMutation(() =>
      exitGeneration === generation && !suspended && !finished
        ? progressSave(offset, true)
        : undefined,
    ).catch(() => {});
  };
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushOnExit();
  });
  window.addEventListener("pagehide", flushOnExit);
  loadMedia();
})();
