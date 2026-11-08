(() => {
  "use strict";

  const video = document.getElementById("b2-video");
  const status = document.getElementById("player-status");
  const configNode = document.getElementById("b2-player-config");
  if (!video || !status || !configNode) return;
  const setLoading = (loading) => {
    if (loading) status.setAttribute("data-loading", "true");
    else status.removeAttribute("data-loading");
  };
  const showLoadingMessage = (message = "Loading video…") => {
    const letters = Array.from(message)
      .map(
        (letter, index) =>
          `<span class="b2-loading-letter" style="--i:${index}">${letter === " " ? " " : letter}</span>`,
      )
      .join("");
    status.innerHTML = `<span class="b2-loading-text"><span aria-hidden="true">${letters}</span><span class="visually-hidden">${message}</span></span>`;
  };

  let config;
  try {
    config = JSON.parse(configNode.textContent);
  } catch (_) {
    setLoading(false);
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
  let captionsEnabled = config.captions_enabled === true;
  let captionsReady = false;
  let captionQueue = Promise.resolve();
  const captionTracks = () => {
    const tracks = [];
    for (let index = 0; index < (video.textTracks?.length || 0); index += 1) {
      const track = video.textTracks[index];
      if (track.kind === "subtitles" || track.kind === "captions")
        tracks.push(track);
    }
    return tracks;
  };
  const restoreCaptions = () => {
    const tracks = captionTracks();
    tracks.forEach((track, index) => {
      track.mode = captionsEnabled && index === 0 ? "showing" : "disabled";
    });
    captionsReady = true;
  };
  const persistCaptions = (enabled) => {
    if (!config.captions_url) return;
    captionQueue = captionQueue
      .catch(() => {})
      .then(() =>
        request(
          config.captions_url,
          "POST",
          { captions_enabled: String(enabled) },
          true,
        ),
      )
      .catch(() => {});
  };
  const onTextTrackChange = () => {
    if (!captionsReady) return;
    const tracks = captionTracks();
    if (!tracks.length) return;
    const enabled = tracks.some((track) => track.mode === "showing");
    if (enabled === captionsEnabled) return;
    captionsEnabled = enabled;
    persistCaptions(enabled);
  };
  video.textTracks?.addEventListener("change", onTextTrackChange);

  let castSourceUrl = null;
  let castSession = null;
  let castLoadKey = null;
  let castLoadSequence = 0;
  let castReady = false;
  let castRemoteActive = false;
  const castButton = document.getElementById("cast-video");
  const setLocalPlaybackEnabled = (enabled) => {
    video.controls = enabled;
    [
      "seek-back",
      "seek-forward",
      "start-over",
      "binge-toggle",
      "airplay-video",
    ].forEach((id) => {
      const control = document.getElementById(id);
      if (control) control.disabled = !enabled;
    });
  };
  const loadCastMedia = () => {
    if (!castReady || !castSession || !castSourceUrl || !resumeReady) return;
    const key = castSourceUrl;
    if (castLoadKey === key) return;
    castLoadKey = key;
    const session = castSession;
    const operation = ++castLoadSequence;
    try {
      const media = new window.chrome.cast.media.MediaInfo(
        castSourceUrl,
        "video/mp4",
      );
      const request = new window.chrome.cast.media.LoadRequest(media);
      request.currentTime = Number.isFinite(video.currentTime)
        ? video.currentTime
        : 0;
      session.loadMedia(request).then(
        () => {
          if (castSession !== session || castLoadSequence !== operation) return;
          video.pause();
          setLocalPlaybackEnabled(false);
          setStatus("Playing on Chromecast");
        },
        () => {
          if (castSession !== session || castLoadSequence !== operation) return;
          castLoadKey = null;
          castRemoteActive = false;
          setLocalPlaybackEnabled(true);
          setStatus(
            "Could not start casting. Local playback is still available.",
          );
        },
      );
    } catch (_) {
      if (castSession !== session || castLoadSequence !== operation) return;
      castLoadKey = null;
      castRemoteActive = false;
      setLocalPlaybackEnabled(true);
      setStatus("Could not start casting. Local playback is still available.");
    }
  };
  const initializeCast = (available) => {
    if (
      !available ||
      castReady ||
      !window.cast?.framework ||
      !window.chrome?.cast?.media
    )
      return;
    try {
      const castContext = window.cast.framework.CastContext.getInstance();
      const sessionStates = window.cast.framework.SessionState;
      castContext.setOptions({
        receiverApplicationId:
          window.chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
        autoJoinPolicy: window.chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
      });
      castContext.addEventListener(
        window.cast.framework.CastContextEventType.SESSION_STATE_CHANGED,
        (event) => {
          if (event.sessionState === sessionStates.SESSION_STARTED) {
            const session = castContext.getCurrentSession();
            if (!session) return;
            if (castSession !== session) {
              castLoadSequence += 1;
              castLoadKey = null;
            }
            castSession = session;
            castRemoteActive = true;
            setLocalPlaybackEnabled(false);
            setStatus("Connecting to Chromecast");
            loadCastMedia();
            return;
          }
          if (event.sessionState === sessionStates.SESSION_RESUMED) {
            const session = castContext.getCurrentSession();
            const currentMedia = session?.getMediaSession?.()?.media;
            if (session && currentMedia?.contentId === castSourceUrl) {
              castSession = session;
              castRemoteActive = true;
              castLoadKey = castSourceUrl;
              setLocalPlaybackEnabled(false);
              setStatus("Playing on Chromecast");
            } else {
              castLoadSequence += 1;
              castSession = null;
              castRemoteActive = false;
              castLoadKey = null;
              setLocalPlaybackEnabled(true);
            }
            return;
          }
          if (event.sessionState === sessionStates.SESSION_ENDED) {
            if (!castSession) return;
            castLoadSequence += 1;
            castSession = null;
            castRemoteActive = false;
            castLoadKey = null;
            setLocalPlaybackEnabled(true);
            setStatus("Casting ended. Press play to continue here.");
            return;
          }
        },
      );
      castReady = true;
      if (castButton) castButton.hidden = false;
    } catch (_) {
      castReady = false;
    }
  };
  window.__onGCastApiAvailable = initializeCast;
  const castSdk = document.createElement("script");
  castSdk.src =
    "https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1";
  castSdk.async = true;
  castSdk.onerror = () => {
    castReady = false;
  };
  document.head?.append(castSdk);

  const airplayButton = document.getElementById("airplay-video");
  if (
    airplayButton &&
    typeof video.webkitShowPlaybackTargetPicker === "function"
  ) {
    video.addEventListener(
      "webkitplaybacktargetavailabilitychanged",
      (event) => {
        airplayButton.hidden = event.availability !== "available";
      },
    );
    airplayButton.addEventListener("click", () =>
      video.webkitShowPlaybackTargetPicker(),
    );
  }

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
    bingeButton.classList.toggle("btn-success", bingeEnabled);
    bingeButton.classList.toggle("btn-danger", !bingeEnabled);
  };
  const loadMedia = () => {
    if (mediaRequest) return mediaRequest;
    setLoading(true);
    showLoadingMessage();
    mediaRequest = Promise.resolve().then(async () => {
      try {
        if (typeof config.media_url !== "string" || !config.media_url)
          throw new Error("Invalid media URL");
        const response = await fetch(config.media_url, {
          method: "GET",
          credentials: "same-origin",
        });
        if (!response.ok) throw new Error("Media request failed");
        const result = await response.json();
        if (
          !result ||
          typeof result.source_url !== "string" ||
          !result.source_url ||
          !Array.isArray(result.subtitle_urls) ||
          result.subtitle_urls.some((url) => typeof url !== "string" || !url)
        )
          throw new Error("Invalid media response");
        captionsReady = false;
        castSourceUrl = result.source_url;
        video
          .querySelectorAll("source, track")
          .forEach((child) => child.remove());
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
          track.default = captionsEnabled && index === 0;
          video.append(track);
          track.track.mode =
            captionsEnabled && index === 0 ? "showing" : "disabled";
        });
        video.load();
        loadCastMedia();
      } catch (_) {
        setLoading(false);
        status.innerHTML =
          'Video could not be loaded. <button class="btn btn-sm btn-outline-light" id="retry-video" type="button">Retry</button>.';
        document
          .getElementById("retry-video")
          ?.addEventListener("click", () => {
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
  const setStatus = (
    message,
    ownerGeneration = generation,
    { fadeOut = false } = {},
  ) => {
    if (ownerGeneration !== generation) return;
    if (
      castRemoteActive &&
      message !== "Connecting to Chromecast" &&
      message !== "Playing on Chromecast"
    )
      return;
    if (fadeOut) {
      status.innerHTML = `<span class="b2-resume-notice">${message}</span>`;
      return;
    }
    status.textContent = message;
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
      setStatus("Could not save playback position", saveGeneration, {
        fadeOut: true,
      }),
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
        setStatus("Marked as viewed", completeGeneration);
      })
      .catch(() => {
        setStatus(
          "Playback finished but progress or viewing status could not be updated",
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
      loadCastMedia();
      setStatus(
        retryOffset > 0 ? "Position loaded" : "Ready to play",
        expectedGeneration,
        { fadeOut: true },
      );
    } catch (_) {
      if (
        expectedGeneration !== generation ||
        loadGeneration !== expectedGeneration ||
        suspended
      )
        return;
      resumeReady = true;
      loadCastMedia();
      setStatus("Position could not be loaded", expectedGeneration);
    }
  };

  showLoadingMessage();
  let retryPending = false;
  video.addEventListener("loadedmetadata", () => {
    setLoading(false);
    restoreCaptions();
    if (suspended || resumeReady || loadGeneration === generation) return;
    const offset = retryPending ? retryOffset : null;
    retryPending = false;
    loadResume(generation, offset);
  });
  video.addEventListener("error", () => {
    setLoading(false);
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
      captionsReady = false;
      loadGeneration = -1;
      setLoading(true);
      showLoadingMessage("Retrying…");
      video.load();
      if (video.readyState >= 1) {
        retryPending = false;
        restoreCaptions();
        loadResume(generation, retryOffset);
      }
    });
  });
  video.addEventListener("play", () => {
    if (castRemoteActive) {
      video.pause();
      return;
    }
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
    if (castRemoteActive) return;
    video.currentTime = Math.max(0, video.currentTime - 10);
  });
  document.getElementById("seek-forward").addEventListener("click", () => {
    if (castRemoteActive) return;
    video.currentTime = Math.min(
      video.duration || Infinity,
      video.currentTime + 10,
    );
  });
  document.getElementById("start-over").addEventListener("click", async () => {
    if (castRemoteActive) return;
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
