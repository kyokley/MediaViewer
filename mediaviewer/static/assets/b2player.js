(() => {
  "use strict";

  const shared = (window.__mediaViewerPlayerShared ||= {
    mutationQueue: Promise.resolve(),
    castScript: null,
    castOptionsConfigured: false,
    captionPreferences: new Map(),
  });
  const api = (window.MediaViewerPlayer = window.MediaViewerPlayer || {});
  let currentDispose = null;
  Object.defineProperty(api, "ready", {
    configurable: true,
    get: () => shared.mutationQueue,
  });
  api.init = () => {
    if (currentDispose) return api.ready;
    currentDispose = initialize(() => {
      currentDispose = null;
    });
    return api.ready;
  };
  api.dispose = () => currentDispose?.();

  const initialize = (onDispose) => {
    const video = document.getElementById("b2-video");
    const status = document.getElementById("player-status");
    const configNode = document.getElementById("b2-player-config");
    if (!video || !status || !configNode) return null;
    let disposed = false;
    const listeners = [];
    const playerCard = video.closest(".b2-player-card");
    const pipButton = document.getElementById("picture-in-picture");
    const pipApi = window.documentPictureInPicture;
    let pipWindow = null;
    let pipPlaceholder = null;
    let pipRequestPending = false;
    const pipSupported =
      typeof pipApi?.requestWindow === "function" && Boolean(playerCard);
    if (pipButton) pipButton.hidden = !pipSupported;
    if (pipSupported) video.disablePictureInPicture = true;
    const updatePipButton = (inPip) => {
      if (!pipButton) return;
      const label = inPip ? "Return player to page" : "Enter picture-in-picture";
      pipButton.setAttribute("aria-label", label);
      pipButton.setAttribute("title", label);
      pipButton.setAttribute("aria-pressed", String(inPip));
      const text = pipButton.querySelector(".b2-control-label");
      if (text) text.textContent = inPip ? "Return to page" : "Picture in picture";
    };
    const restorePip = () => {
      if (!pipPlaceholder) return;
      pipPlaceholder.parentNode?.insertBefore(playerCard, pipPlaceholder);
      pipPlaceholder.remove();
      pipPlaceholder = null;
      playerCard.classList.remove("b2-player-card-pip");
      pipWindow = null;
      updatePipButton(false);
    };
    const enterPip = async () => {
      if (!alive() || pipRequestPending || !pipSupported) return;
      if (pipWindow && !pipWindow.closed) {
        pipWindow.close();
        restorePip();
        return;
      }
      pipRequestPending = true;
      let nextWindow;
      try {
        nextWindow = await pipApi.requestWindow({ width: 480, height: 420 });
        if (!alive()) { nextWindow.close(); return; }
        pipWindow = nextWindow;
        const doc = nextWindow.document;
        doc.title = document.title;
        doc.documentElement.lang = document.documentElement.lang;
        doc.documentElement.className = document.documentElement.className;
        for (const attribute of document.documentElement.attributes)
          doc.documentElement.setAttribute(attribute.name, attribute.value);
        const base = doc.createElement("base");
        base.href = document.baseURI;
        doc.head.append(base);
        const referrer = document.querySelector('meta[name="referrer"]');
        if (referrer) doc.head.append(referrer.cloneNode(true));
        for (const node of document.head.querySelectorAll('link[rel="stylesheet"], style')) {
          try { doc.head.append(node.cloneNode(true)); } catch (_) { /* stylesheet may be cross-origin */ }
        }
        const bodyStyle = getComputedStyle(document.body);
        doc.body.style.margin = "0";
        doc.body.style.padding = "0";
        doc.body.style.background = bodyStyle.backgroundColor;
        doc.body.classList.add("b2-pip-document");
        pipPlaceholder = document.createComment("B2 player location");
        playerCard.parentNode.insertBefore(pipPlaceholder, playerCard);
        doc.body.append(playerCard);
        playerCard.classList.add("b2-player-card-pip");
        updatePipButton(true);
        nextWindow.addEventListener("pagehide", restorePip, { once: true });
      } catch (_) {
        try { nextWindow?.close(); } catch (_) { /* window may already be closed */ }
        restorePip();
        if (alive()) setStatus("Could not open picture-in-picture");
      } finally {
        pipRequestPending = false;
      }
    };
    const listen = (target, type, handler, options) => {
      if (!target?.addEventListener) return;
      target.addEventListener(type, handler, options);
      listeners.push(() =>
        target.removeEventListener?.(type, handler, options),
      );
    };
    listen(pipButton, "click", enterPip);
    const alive = () => !disposed;
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
    const progressGet = async () => {
      await shared.mutationQueue.catch(() => {});
      return request(config.progress_url, "GET");
    };
    const progressSave = (offset, keepalive = false) =>
      request(
        config.progress_url,
        "POST",
        { guid: config.guid, offset: String(offset) },
        keepalive,
      );
    const progressClear = () => request(config.progress_url, "DELETE");
    const captionKey = config.captions_url;
    let captionsEnabled =
      captionKey && shared.captionPreferences.has(captionKey)
        ? shared.captionPreferences.get(captionKey)
        : config.captions_enabled === true;
    let captionsReady = false;
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
      updateCaptionsButton();
    };
    const persistCaptions = (enabled) => {
      if (!config.captions_url) return;
      shared.captionPreferences.set(captionKey, enabled);
      shared.mutationQueue = shared.mutationQueue
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
      if (castRemoteActive) {
        updateCaptionsButton();
        return;
      }
      const enabled = tracks.some((track) => track.mode === "showing");
      if (tracks.length && enabled !== captionsEnabled) {
        captionsEnabled = enabled;
        persistCaptions(enabled);
      }
      updateCaptionsButton();
    };
    listen(video.textTracks, "change", onTextTrackChange);

    let castSourceUrl = null;
    let castSubtitleUrls = [];
    let castSession = null;
    let castLoadKey = null;
    let castLoadSequence = 0;
    let castReady = false;
    let castContext = null;
    let castState = null;
    let castRequestPending = false;
    let castRemoteActive = false;
    let castMediaSession = null;
    let castMediaUpdate = null;
    let castSessionUpdate = null;
    let seekPending = false;
    let captionsPending = false;
    let playPausePending = false;
    let localPlayPending = false;
    let localPlaySequence = 0;
    const castButton = document.getElementById("cast-video");
    const castButtonLabel = castButton?.querySelector(".b2-control-label");
    const playPauseButton = document.getElementById("play-pause");
    const playPauseLabel = playPauseButton?.querySelector(".b2-control-label");
    const castCaptionsButton = document.getElementById("cast-captions-toggle");
    const castCaptionsLabel =
      castCaptionsButton?.querySelector(".b2-control-label");
    let airplayAvailability = null;
    const airplaySupported =
      typeof video.webkitShowPlaybackTargetPicker === "function";
    const isAirplayActive = () =>
      airplaySupported && video.webkitCurrentPlaybackTargetIsWireless === true;
    const getWirelessRoute = () => {
      const castStates = window.cast?.framework?.CastState;
      const connected =
        castState === castStates?.CONNECTED ||
        Boolean(castContext?.getCurrentSession?.());
      const castAvailable =
        castReady &&
        typeof castContext?.requestSession === "function" &&
        castState != null &&
        castState !== castStates?.NO_DEVICES_AVAILABLE &&
        castState !== castStates?.CONNECTING;
      const airplayAvailable =
        airplaySupported &&
        (isAirplayActive() || airplayAvailability !== false);
      if (connected) return "cast";
      if (isAirplayActive()) return "airplay";
      if (castAvailable) return "cast";
      if (airplayAvailable) return "airplay";
      return null;
    };
    const updateWirelessButton = () => {
      if (!castButton) return;
      const route = getWirelessRoute();
      let accessibleLabel = "Choose playback device";
      let connected = false;
      if (route === "cast") {
        connected =
          castState === window.cast?.framework?.CastState?.CONNECTED ||
          Boolean(castContext?.getCurrentSession?.());
        accessibleLabel = connected ? "Chromecast connected" : "Cast video";
      } else if (route === "airplay") {
        connected = isAirplayActive();
        accessibleLabel = connected ? "AirPlay connected" : "AirPlay video";
      }
      if (castButtonLabel) {
        castButtonLabel.innerHTML =
          route === "airplay"
            ? '<svg class="b2-airplay-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="2"></rect><path d="M12 14 3 23h18z" fill="currentColor"></path></svg>'
            : '<svg class="b2-chromecast-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="9" y="3" width="12" height="12" rx="1.5" fill="none" stroke="currentColor" stroke-width="2"></rect><path d="M3 14a9 9 0 0 1 9 9M3 19a4 4 0 0 1 4 4" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="2"></path><circle cx="3" cy="23" r="1" fill="currentColor"></circle></svg>';
      }
      castButton.setAttribute("aria-label", accessibleLabel);
      castButton.setAttribute("title", accessibleLabel);
      castButton.classList.toggle("active", connected);
      const castConnecting =
        castState === window.cast?.framework?.CastState?.CONNECTING;
      castButton.disabled =
        !alive() || !route || castRequestPending || castConnecting;
    };
    const renderPlaybackButton = (playing) => {
      if (!playPauseButton || !playPauseLabel) return;
      const label = playing ? "Pause" : "Play";
      const icon = playing ? "pause" : "play";
      playPauseLabel.innerHTML = `<i class="bi-${icon}-fill" aria-hidden="true"></i> ${label}`;
      playPauseButton.setAttribute(
        "aria-label",
        playing ? "Pause video" : "Play video",
      );
    };
    if (playPauseButton) {
      playPauseButton.disabled = true;
      renderPlaybackButton(false);
    }
    if (castCaptionsButton) {
      castCaptionsButton.disabled = true;
      if (castCaptionsLabel) castCaptionsLabel.textContent = "Captions: Off";
      castCaptionsButton.setAttribute("aria-pressed", "false");
    }
    const getRemoteMedia = () => {
      const media = castMediaSession;
      return alive() &&
        castRemoteActive &&
        castSession &&
        media &&
        media.media?.contentId === castSourceUrl
        ? media
        : null;
    };
    const remoteTextTracks = (media) =>
      (media?.media?.tracks || []).filter(
        (track) => track.type === window.chrome?.cast?.media?.TrackType?.TEXT,
      );
    const activeRemoteTextTracks = (media) => {
      const ids = media?.activeTrackIds || [];
      return remoteTextTracks(media).filter((track) =>
        ids.includes(track.trackId),
      );
    };
    const updatePlaybackButton = () => {
      if (!playPauseButton) return;
      const sdkMedia = window.chrome?.cast?.media;
      if (castRemoteActive) {
        const media = getRemoteMedia();
        const state = media?.playerState;
        const playing =
          state === sdkMedia?.PlayerState?.PLAYING ||
          state === sdkMedia?.PlayerState?.BUFFERING;
        const paused = state === sdkMedia?.PlayerState?.PAUSED;
        renderPlaybackButton(playing);
        const canPause = Boolean(
          media &&
          playing &&
          sdkMedia?.MediaCommand?.PAUSE &&
          media.supportsCommand?.(sdkMedia.MediaCommand.PAUSE),
        );
        playPauseButton.disabled =
          !media ||
          (!playing && !paused) ||
          (playing && !canPause) ||
          playPausePending;
        return;
      }
      const playing = !video.paused;
      renderPlaybackButton(playing);
      playPauseButton.disabled =
        !alive() || !resumeReady || suspended || localPlayPending;
    };
    const updateCaptionsButton = () => {
      if (!castCaptionsButton) return;
      if (castRemoteActive) {
        const media = getRemoteMedia();
        const tracks = remoteTextTracks(media);
        const enabled = activeRemoteTextTracks(media).length > 0;
        castCaptionsButton.disabled =
          !media || tracks.length === 0 || captionsPending;
        if (castCaptionsLabel)
          castCaptionsLabel.textContent = `Captions: ${enabled ? "On" : "Off"}`;
        castCaptionsButton.setAttribute("aria-pressed", String(enabled));
        return;
      }
      const tracks = captionTracks();
      const enabled = tracks.some((track) => track.mode === "showing");
      castCaptionsButton.disabled = !captionsReady || tracks.length === 0;
      if (castCaptionsLabel)
        castCaptionsLabel.textContent = `Captions: ${enabled ? "On" : "Off"}`;
      castCaptionsButton.setAttribute("aria-pressed", String(enabled));
    };
    const updateCastControls = () => {
      const media = getRemoteMedia();
      const sdkMedia = window.chrome?.cast?.media;
      if (!castRemoteActive) {
        updatePlaybackButton();
        updateCaptionsButton();
        return;
      }
      const seekSupported = Boolean(
        media &&
        sdkMedia?.MediaCommand &&
        media.supportsCommand?.(sdkMedia.MediaCommand.SEEK),
      );
      ["seek-back", "seek-forward"].forEach((id) => {
        const button = document.getElementById(id);
        if (button) button.disabled = !media || !seekSupported || seekPending;
      });
      updatePlaybackButton();
      updateCaptionsButton();
    };
    const clearCurrentMedia = () => {
      if (castMediaSession && castMediaUpdate)
        castMediaSession.removeUpdateListener?.(castMediaUpdate);
      castMediaSession = null;
      castMediaUpdate = null;
      seekPending = false;
      captionsPending = false;
      playPausePending = false;
      updateCastControls();
    };
    const clearRemoteMedia = () => {
      clearCurrentMedia();
      if (castSession && castSessionUpdate)
        castSession.removeEventListener?.(
          window.cast?.framework?.SessionEventType?.MEDIA_SESSION,
          castSessionUpdate,
        );
      castSessionUpdate = null;
    };
    const attachRemoteMedia = (session, media) => {
      if (castSession !== session || !castRemoteActive) return;
      if (castMediaSession !== media) {
        clearCurrentMedia();
        castSession = session;
        if (media?.media?.contentId === castSourceUrl) {
          castMediaSession = media;
          castMediaUpdate = (isAlive) => {
            if (castSession !== session || castMediaSession !== media) return;
            if (!isAlive) {
              clearCurrentMedia();
              return;
            }
            updateCastControls();
          };
          media.addUpdateListener?.(castMediaUpdate);
        }
      }
      updateCastControls();
    };
    const refreshRemoteMedia = (session) => {
      if (castSession !== session || !castRemoteActive) return;
      attachRemoteMedia(session, session.getMediaSession?.());
    };
    const setLocalPlaybackEnabled = (enabled) => {
      video.controls = enabled;
      if (!enabled) {
        localPlaySequence += 1;
        localPlayPending = false;
      }
      ["seek-back", "seek-forward", "start-over", "binge-toggle"].forEach(
        (id) => {
          const control = document.getElementById(id);
          if (control) control.disabled = !enabled;
        },
      );
      updateCastControls();
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
        media.tracks = castSubtitleUrls.map((url, index) => {
          const track = new window.chrome.cast.media.Track(
            index + 1,
            window.chrome.cast.media.TrackType.TEXT,
          );
          track.trackContentId = url;
          track.trackContentType = "text/vtt";
          track.subtype = window.chrome.cast.media.TextTrackType.SUBTITLES;
          track.language = "en";
          track.name = `English${index ? ` ${index + 1}` : ""}`;
          return track;
        });
        const request = new window.chrome.cast.media.LoadRequest(media);
        request.activeTrackIds =
          captionsEnabled && media.tracks.length ? [1] : [];
        request.currentTime = Number.isFinite(video.currentTime)
          ? video.currentTime
          : 0;
        session.loadMedia(request).then(
          (errorCode) => {
            if (
              !alive() ||
              castSession !== session ||
              castLoadSequence !== operation
            )
              return;
            if (errorCode != null) {
              castLoadKey = null;
              clearRemoteMedia();
              castRemoteActive = false;
              setLocalPlaybackEnabled(true);
              setStatus(
                "Could not start casting. Local playback is still available.",
              );
              return;
            }
            video.pause();
            setLocalPlaybackEnabled(false);
            setStatus("Playing on Chromecast");
            refreshRemoteMedia(session);
          },
          () => {
            if (
              !alive() ||
              castSession !== session ||
              castLoadSequence !== operation
            )
              return;
            castLoadKey = null;
            clearRemoteMedia();
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
        clearRemoteMedia();
        castRemoteActive = false;
        setLocalPlaybackEnabled(true);
        setStatus(
          "Could not start casting. Local playback is still available.",
        );
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
        castContext = window.cast.framework.CastContext.getInstance();
        const sessionStates = window.cast.framework.SessionState;
        if (!shared.castOptionsConfigured) {
          castContext.setOptions({
            receiverApplicationId:
              window.chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
            autoJoinPolicy: window.chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
          });
          shared.castOptionsConfigured = true;
        }
        const castEvents = window.cast.framework.CastContextEventType;
        listen(castContext, castEvents.CAST_STATE_CHANGED, (event) => {
          castState = event.castState;
          updateWirelessButton();
        });
        castState = castContext.getCastState();
        listen(castContext, castEvents.SESSION_STATE_CHANGED, (event) => {
          if (event.sessionState === sessionStates.SESSION_STARTED) {
            const session = castContext.getCurrentSession();
            if (!session) return;
            if (castSession !== session) {
              clearRemoteMedia();
              castLoadSequence += 1;
              castLoadKey = null;
            }
            castSession = session;
            castRemoteActive = true;
            if (!castSessionUpdate) {
              castSessionUpdate = (mediaEvent) => {
                if (castSession !== session || !castRemoteActive) return;
                attachRemoteMedia(session, mediaEvent.mediaSession);
              };
              session.addEventListener?.(
                window.cast.framework.SessionEventType?.MEDIA_SESSION,
                castSessionUpdate,
              );
            }
            setLocalPlaybackEnabled(false);
            updateCastControls();
            setStatus("Connecting to Chromecast");
            updateWirelessButton();
            loadCastMedia();
            return;
          }
          if (event.sessionState === sessionStates.SESSION_RESUMED) {
            const session = castContext.getCurrentSession();
            const currentMedia = session?.getMediaSession?.()?.media;
            if (session && currentMedia?.contentId === castSourceUrl) {
              if (castSession !== session) clearRemoteMedia();
              castSession = session;
              castRemoteActive = true;
              castLoadKey = castSourceUrl;
              if (!castSessionUpdate) {
                castSessionUpdate = (mediaEvent) => {
                  if (castSession !== session || !castRemoteActive) return;
                  attachRemoteMedia(session, mediaEvent.mediaSession);
                };
                session.addEventListener?.(
                  window.cast.framework.SessionEventType?.MEDIA_SESSION,
                  castSessionUpdate,
                );
              }
              attachRemoteMedia(session, session.getMediaSession?.());
              video.pause();
              setLocalPlaybackEnabled(false);
              setStatus("Playing on Chromecast");
              updateWirelessButton();
            } else {
              castLoadSequence += 1;
              clearRemoteMedia();
              castSession = null;
              castRemoteActive = false;
              castLoadKey = null;
              setLocalPlaybackEnabled(true);
              updateWirelessButton();
            }
            return;
          }
          if (event.sessionState === sessionStates.SESSION_ENDED) {
            if (!castSession) return;
            castLoadSequence += 1;
            clearRemoteMedia();
            castSession = null;
            castRemoteActive = false;
            castLoadKey = null;
            setLocalPlaybackEnabled(true);
            setStatus("Casting ended. Press play to continue here.");
            updateWirelessButton();
            return;
          }
        });
        castReady = true;
        updateWirelessButton();
      } catch (_) {
        castReady = false;
        updateWirelessButton();
      }
    };
    const previousCastCallback = window.__onGCastApiAvailable;
    const castCallback = (available) => {
      if (!alive()) return;
      initializeCast(available);
      updateWirelessButton();
    };
    window.__onGCastApiAvailable = castCallback;
    if (!shared.castScript) {
      const castSdk = document.createElement("script");
      castSdk.src =
        "https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1";
      castSdk.async = true;
      shared.castScript = castSdk;
      document.head?.append(castSdk);
    }

    if (airplaySupported) {
      listen(video, "webkitplaybacktargetavailabilitychanged", (event) => {
        airplayAvailability = event.availability === "available";
        updateWirelessButton();
      });
      listen(video, "webkitcurrentplaybacktargetiswirelesschanged", () =>
        updateWirelessButton(),
      );
    }
    listen(castButton, "click", () => {
      if (!alive() || castRequestPending) return;
      if (castState === window.cast?.framework?.CastState?.CONNECTING) return;
      const route = getWirelessRoute();
      if (route === "airplay") {
        try {
          video.webkitShowPlaybackTargetPicker();
          if (status.textContent === "Could not open AirPlay picker")
            setStatus("");
        } catch (_) {
          setStatus("Could not open AirPlay picker");
        }
        return;
      }
      if (route !== "cast" || typeof castContext?.requestSession !== "function")
        return;
      castRequestPending = true;
      updateWirelessButton();
      const failed = (error) => {
        if (!alive()) return;
        castRequestPending = false;
        updateWirelessButton();
        const cancelCode = window.chrome?.cast?.ErrorCode?.CANCEL;
        if (
          (cancelCode !== undefined &&
            (error === cancelCode || error?.code === cancelCode)) ||
          error === "CANCEL"
        )
          return;
        setStatus("Could not connect to Chromecast");
      };
      let request;
      try {
        request = castContext.requestSession();
      } catch (error) {
        failed(error);
        return;
      }
      Promise.resolve(request).then(() => {
        if (!alive()) return;
        castRequestPending = false;
        updateWirelessButton();
        if (status.textContent === "Could not connect to Chromecast")
          setStatus("");
      }, failed);
    });
    updateWirelessButton();

    let resumeReady = false;
    let suspended = false;
    let finished = false;
    let viewedSent = false;
    let bingeEnabled = Boolean(config.binge_mode && config.next_url);
    let generation = 0;
    let loadGeneration = -1;
    let timer = null;
    let completionPromise = null;
    let retryOffset = 0;
    let mediaRequest = null;
    const bingeButton = document.getElementById("binge-toggle");
    const bingeButtonLabel = bingeButton?.querySelector(".b2-control-label");
    const updateBingeButton = () => {
      if (!bingeButton || !bingeButtonLabel) return;
      bingeButtonLabel.textContent = `Binge mode: ${bingeEnabled ? "On" : "Off"}`;
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
          if (!alive()) return;
          if (
            !result ||
            typeof result.source_url !== "string" ||
            !result.source_url ||
            !Array.isArray(result.subtitle_urls) ||
            result.subtitle_urls.some((url) => typeof url !== "string" || !url)
          )
            throw new Error("Invalid media response");
          captionsReady = false;
          updateCaptionsButton();
          clearCurrentMedia();
          castSourceUrl = result.source_url;
          castSubtitleUrls = result.subtitle_urls;
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
          if (!alive()) return;
          setLoading(false);
          status.innerHTML =
            'Video could not be loaded <button class="btn btn-sm btn-outline-light" id="retry-video" type="button">Retry</button>';
          document
            .getElementById("retry-video")
            ?.addEventListener("click", () => {
              if (!alive()) return;
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
      if (!alive() || ownerGeneration !== generation) return;
      if (
        castRemoteActive &&
        message !== "Connecting to Chromecast" &&
        message !== "Playing on Chromecast" &&
        message !== "" &&
        message !== "Could not seek on Chromecast" &&
        message !== "Could not change Chromecast captions" &&
        message !== "Could not play on Chromecast" &&
        message !== "Could not pause on Chromecast" &&
        message !== "Could not connect to Chromecast" &&
        message !== "Could not open AirPlay picker"
      )
        return;
      if (fadeOut) {
        status.innerHTML = `<span class="b2-resume-notice">${message}</span>`;
        return;
      }
      status.textContent = message;
    };
    const enqueueMutation = (callback) => {
      shared.mutationQueue = shared.mutationQueue
        .catch(() => {})
        .then(callback);
      return shared.mutationQueue;
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
        !alive() ||
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
          if (alive() && completeGeneration === generation) viewedSent = true;
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
      if (!alive() || !bingeEnabled || !config.next_url) return;
      const nextUrl = new URL(config.next_url, document.baseURI).href;
      const nextAnchor = Array.from(
        document.querySelectorAll(".b2-episode-nav a[href]"),
      ).find((anchor) => anchor.href === nextUrl);
      if (window.htmx && nextAnchor) nextAnchor.click();
      else window.location.assign(config.next_url);
    };
    const loadResume = async (expectedGeneration, offsetOnLoad = null) => {
      resumeReady = false;
      updateCastControls();
      loadGeneration = expectedGeneration;
      try {
        const result =
          offsetOnLoad === null
            ? await progressGet()
            : { offset: offsetOnLoad };
        if (
          !alive() ||
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
        updateCastControls();
        loadCastMedia();
        setStatus(
          retryOffset > 0 ? "Position loaded" : "Ready to play",
          expectedGeneration,
          { fadeOut: true },
        );
      } catch (_) {
        if (
          !alive() ||
          expectedGeneration !== generation ||
          loadGeneration !== expectedGeneration ||
          suspended
        )
          return;
        resumeReady = true;
        updateCastControls();
        loadCastMedia();
        setStatus("Position could not be loaded", expectedGeneration);
      }
    };

    showLoadingMessage();
    let retryPending = false;
    listen(video, "loadedmetadata", () => {
      if (!alive()) return;
      setLoading(false);
      restoreCaptions();
      if (suspended || resumeReady || loadGeneration === generation) return;
      const offset = retryPending ? retryOffset : null;
      retryPending = false;
      loadResume(generation, offset);
    });
    listen(video, "error", () => {
      if (!alive()) return;
      resumeReady = false;
      localPlaySequence += 1;
      localPlayPending = false;
      updateCastControls();
      setLoading(false);
      status.innerHTML =
        'Video could not be loaded <button class="btn btn-sm btn-outline-light" id="retry-video" type="button">Retry</button>';
      listen(document.getElementById("retry-video"), "click", () => {
        if (!alive()) return;
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
        updateCastControls();
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
    listen(video, "play", () => {
      if (!alive()) return;
      if (castRemoteActive) {
        video.pause();
        return;
      }
      localPlaySequence += 1;
      localPlayPending = false;
      updatePlaybackButton();
      if (status.textContent === "Could not play video") setStatus("");
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
    listen(video, "pause", () => {
      if (!alive()) return;
      localPlaySequence += 1;
      localPlayPending = false;
      updatePlaybackButton();
      if (status.textContent === "Could not pause video") setStatus("");
      saveProgress();
    });
    listen(video, "timeupdate", () => {
      if (!alive()) return;
      if (
        resumeReady &&
        !suspended &&
        Number.isFinite(video.duration) &&
        video.duration > 0 &&
        video.currentTime / video.duration >= 0.95
      )
        complete();
    });
    listen(video, "ended", () => {
      updatePlaybackButton();
      ended();
    });
    listen(playPauseButton, "click", () => {
      if (!alive()) return;
      if (castRemoteActive) {
        controlRemotePlayback();
        return;
      }
      if (!resumeReady || suspended || localPlayPending) return;
      if (!video.paused) {
        localPlaySequence += 1;
        localPlayPending = false;
        try {
          video.pause();
          updatePlaybackButton();
          if (status.textContent === "Could not pause video") setStatus("");
        } catch (_) {
          updatePlaybackButton();
          setStatus("Could not pause video");
        }
        return;
      }
      const operation = ++localPlaySequence;
      localPlayPending = true;
      updatePlaybackButton();
      const fail = () => {
        if (
          !alive() ||
          operation !== localPlaySequence ||
          castRemoteActive ||
          !resumeReady ||
          suspended
        )
          return;
        localPlayPending = false;
        updatePlaybackButton();
        setStatus("Could not play video");
      };
      try {
        Promise.resolve(video.play()).then(() => {
          if (!alive() || operation !== localPlaySequence || castRemoteActive)
            return;
          localPlayPending = false;
          updatePlaybackButton();
          if (status.textContent === "Could not play video") setStatus("");
        }, fail);
      } catch (_) {
        fail();
      }
    });
    function controlRemotePlayback() {
      const media = getRemoteMedia();
      const sdkMedia = window.chrome?.cast?.media;
      if (!media || playPausePending) return;
      const state = media.playerState;
      const isPlaying =
        state === sdkMedia?.PlayerState?.PLAYING ||
        state === sdkMedia?.PlayerState?.BUFFERING;
      const isPaused = state === sdkMedia?.PlayerState?.PAUSED;
      if (!isPlaying && !isPaused) return;
      if (
        isPlaying &&
        (!sdkMedia?.MediaCommand?.PAUSE ||
          !media.supportsCommand?.(sdkMedia.MediaCommand.PAUSE))
      )
        return;
      const session = castSession;
      const action = isPlaying ? "pause" : "play";
      const fail = () => {
        if (castSession !== session || getRemoteMedia() !== media) return;
        playPausePending = false;
        updateCastControls();
        setStatus(`Could not ${action} on Chromecast`);
      };
      const success = () => {
        if (castSession !== session || getRemoteMedia() !== media) return;
        playPausePending = false;
        updateCastControls();
        if (
          status.textContent === "Could not pause on Chromecast" ||
          status.textContent === "Could not play on Chromecast"
        )
          setStatus("");
      };
      playPausePending = true;
      updateCastControls();
      try {
        media[action](null, success, fail);
      } catch (_) {
        fail();
      }
    }
    listen(document.getElementById("seek-back"), "click", () => {
      if (!alive()) return;
      if (castRemoteActive) {
        seekRemote(-10);
        return;
      }
      video.currentTime = Math.max(0, video.currentTime - 10);
    });
    listen(document.getElementById("seek-forward"), "click", () => {
      if (!alive()) return;
      if (castRemoteActive) {
        seekRemote(10);
        return;
      }
      video.currentTime = Math.min(
        video.duration || Infinity,
        video.currentTime + 10,
      );
    });
    function seekRemote(delta) {
      const media = getRemoteMedia();
      const sdkMedia = window.chrome?.cast?.media;
      if (
        !media ||
        seekPending ||
        !sdkMedia?.MediaCommand ||
        !media.supportsCommand?.(sdkMedia.MediaCommand.SEEK)
      )
        return;
      const duration = media.media?.duration;
      const estimated = media.getEstimatedTime?.();
      if (!Number.isFinite(estimated)) return;
      const request = new sdkMedia.SeekRequest();
      request.currentTime = Math.max(
        0,
        Math.min(
          Number.isFinite(duration) ? duration : Infinity,
          estimated + delta,
        ),
      );
      const state = media.playerState;
      if (state === sdkMedia.PlayerState?.PAUSED)
        request.resumeState = sdkMedia.ResumeState?.PLAYBACK_PAUSE;
      else if (state === sdkMedia.PlayerState?.PLAYING)
        request.resumeState = sdkMedia.ResumeState?.PLAYBACK_START;
      seekPending = true;
      updateCastControls();
      const session = castSession;
      const fail = () => {
        if (castSession !== session || getRemoteMedia() !== media) return;
        seekPending = false;
        updateCastControls();
        setStatus("Could not seek on Chromecast");
      };
      try {
        media.seek(
          request,
          () => {
            if (castSession !== session || getRemoteMedia() !== media) return;
            seekPending = false;
            updateCastControls();
            if (status.textContent === "Could not seek on Chromecast")
              setStatus("Playing on Chromecast");
          },
          fail,
        );
      } catch (_) {
        fail();
      }
    }
    listen(castCaptionsButton, "click", () => {
      if (!alive()) return;
      if (!castRemoteActive) {
        const tracks = captionTracks();
        if (!captionsReady || !tracks.length) return;
        const enabled = !tracks.some((track) => track.mode === "showing");
        tracks.forEach((track, index) => {
          track.mode = enabled && index === 0 ? "showing" : "disabled";
        });
        captionsEnabled = enabled;
        persistCaptions(enabled);
        updateCaptionsButton();
        return;
      }
      const media = getRemoteMedia();
      const sdkMedia = window.chrome?.cast?.media;
      if (
        !media ||
        captionsPending ||
        !remoteTextTracks(media).length ||
        !sdkMedia?.EditTracksInfoRequest
      )
        return;
      const active = media.activeTrackIds || [];
      const activeText = remoteTextTracks(media).filter((track) =>
        active.includes(track.trackId),
      );
      const preserve = active.filter(
        (id) => !remoteTextTracks(media).some((track) => track.trackId === id),
      );
      const next = activeText.length
        ? preserve
        : [...preserve, remoteTextTracks(media)[0].trackId];
      const request = new sdkMedia.EditTracksInfoRequest(next);
      captionsPending = true;
      updateCastControls();
      const session = castSession;
      const fail = () => {
        if (castSession !== session || getRemoteMedia() !== media) return;
        captionsPending = false;
        updateCastControls();
        setStatus("Could not change Chromecast captions");
      };
      try {
        media.editTracksInfo(
          request,
          () => {
            if (castSession !== session || getRemoteMedia() !== media) return;
            captionsPending = false;
            captionsEnabled = next.some((id) =>
              remoteTextTracks(media).some((track) => track.trackId === id),
            );
            persistCaptions(captionsEnabled);
            captionTracks().forEach((track, index) => {
              track.mode =
                captionsEnabled && index === 0 ? "showing" : "disabled";
            });
            updateCastControls();
            if (status.textContent === "Could not change Chromecast captions")
              setStatus("Playing on Chromecast");
          },
          fail,
        );
      } catch (_) {
        fail();
      }
    });
    listen(document.getElementById("start-over"), "click", async () => {
      if (!alive()) return;
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
      if (!alive() || restartGeneration !== generation) return;
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
      listen(bingeButton, "click", () => {
        if (!alive()) return;
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
      enqueueMutation(() => progressSave(offset, true)).catch(() => {});
    };
    listen(document, "visibilitychange", () => {
      if (document.visibilityState === "hidden") flushOnExit();
    });
    listen(window, "pagehide", flushOnExit);
    listen(window, "pagehide", () => {
      if (pipWindow && !pipWindow.closed) pipWindow.close();
      restorePip();
    });
    loadMedia();
    if (window.cast?.framework && window.chrome?.cast?.media)
      initializeCast(true);
    return () => {
      if (disposed) return;
      if (pipWindow && !pipWindow.closed) pipWindow.close();
      restorePip();
      flushOnExit();
      disposed = true;
      localPlaySequence += 1;
      localPlayPending = false;
      updatePlaybackButton();
      stopTimer();
      listeners.splice(0).forEach((remove) => remove());
      video.pause();
      video.removeAttribute?.("src");
      video
        .querySelectorAll("source, track")
        .forEach((child) => child.remove());
      video.load();
      castLoadSequence += 1;
      clearRemoteMedia();
      castSession = null;
      castRemoteActive = false;
      if (window.__onGCastApiAvailable === castCallback)
        window.__onGCastApiAvailable = previousCastCallback;
      onDispose();
    };
  };

  api.init();
})();
