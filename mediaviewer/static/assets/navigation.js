(function installMediaViewerNavigation(window, document) {
  "use strict";
  if (window.MediaViewerNavigation) return;

  var initializers = [];
  var pendingMount = false;
  var disposedTransition = false;
  var pendingTitle = null;
  var pendingHistoryRequest = null;
  var epoch = window.__mediaViewerPageEpoch || 0;
  var pagePath =
    /^\/mediaviewer\/(?:|movies\/|movies\/genre\/\d+\/|moviedetail\/\d+\/|tvshows\/|tvshows\/summary\/|tvshows\/genre\/\d+\/|tvshows\/\d+\/|tvdetail\/\d+\/|collection\/\d+\/|settings\/|requests\/|b2player\/[0-9A-Za-z]+\/)$/;
  var postPaths = new Set([
    "/mediaviewer/submitsettings/",
    "/mediaviewer/submitnewuser/",
    "/mediaviewer/addrequests/",
    "/mediaviewer/submitsitewidemessage/",
  ]);

  function classify(method, value) {
    var url;
    try {
      url = new URL(value, window.location.href);
    } catch (_) {
      return false;
    }
    if (url.origin !== window.location.origin || url.hash) return false;
    method = String(method || "GET").toUpperCase();
    return method === "GET"
      ? pagePath.test(url.pathname)
      : method === "POST" && postPaths.has(url.pathname);
  }

  function root() {
    return document.getElementById("app-content");
  }
  function responseRoot(html) {
    var parsed = new DOMParser().parseFromString(html || "", "text/html");
    var roots = parsed.querySelectorAll("#app-content");
    return roots.length === 1 ? roots[0] : null;
  }
  function showError(message) {
    var error = document.getElementById("navigation-error");
    if (error) {
      error.classList.remove("hidden");
      error.hidden = false;
      var node = error.querySelector("#navigation-error-message");
      if (node) node.textContent = message;
    }
  }
  function clearError() {
    var error = document.getElementById("navigation-error");
    if (!error) return;
    error.classList.add("hidden");
    error.hidden = true;
    var node = error.querySelector("#navigation-error-message");
    if (node) node.textContent = "";
  }
  function clearLoading() {
    var current = root();
    if (current) current.removeAttribute("aria-busy");
    var indicator = document.getElementById("navigation-indicator");
    if (indicator) indicator.hidden = true;
  }
  function cancelPendingHistoryRequest() {
    var pending = pendingHistoryRequest;
    pendingHistoryRequest = null;
    if (pending) {
      pending.cancelled = true;
      pending.xhr.abort();
    }
  }
  function hideOutgoingModals() {
    var current = root();
    var Modal = window.bootstrap && window.bootstrap.Modal;
    if (!current || !Modal) return;
    current.querySelectorAll(".modal.show").forEach(function (element) {
      var instance = Modal.getInstance(element);
      if (!instance) return;
      // Bootstrap hide() and backdrop cleanup are transition-delayed for .fade modals.
      // Make both callbacks synchronous so they restore body lock before HTMX removes root.
      element.classList.remove("fade");
      if (instance._backdrop && instance._backdrop._config) {
        instance._backdrop._config.isAnimated = false;
      }
      instance.hide();
      instance.dispose();
    });
  }
  function dispose() {
    if (disposedTransition) return;
    disposedTransition = true;
    hideOutgoingModals();
    epoch += 1;
    window.__mediaViewerPageEpoch = epoch;
    initializers = [];
    if (window.MediaViewerPlayer && window.MediaViewerPlayer.dispose)
      window.MediaViewerPlayer.dispose();
    var $ = window.jQuery;
    if (!$) return;
    $(".carousel.slick-initialized").slick("unslick");
    $(".img-preview, .skip-btn").popover("dispose");
    if ($.fn.DataTable)
      $(".dataTable").each(function () {
        if ($.fn.DataTable.isDataTable(this)) $(this).DataTable().destroy();
      });
  }
  function applyRootMetadata(target, source) {
    if (target !== source) {
      var attributes = Array.from(source.attributes);
      Array.from(target.attributes).forEach(function (attribute) {
        if (attribute.name !== "id" && attribute.name !== "aria-busy")
          target.removeAttribute(attribute.name);
      });
      attributes.forEach(function (attribute) {
        if (attribute.name === "id" || attribute.name === "aria-busy") return;
        if (attribute.name === "class") target.className = attribute.value;
        else target.setAttribute(attribute.name, attribute.value);
      });
    }
    var referrerPolicy = document.querySelector('meta[name="referrer"]');
    if (referrerPolicy) {
      referrerPolicy.content = target.querySelector("#b2-video")
        ? "no-referrer"
        : "same-origin";
    }
    var theme = target.dataset.theme || "";
    document.documentElement.dataset.bsTheme = theme;
    document.documentElement.classList.toggle("light", theme === "light");
    document.documentElement.classList.toggle("dark", theme === "dark");
    var tokenCookie = document.cookie.split("; ").find(function (item) {
      return item.indexOf("csrftoken=") === 0;
    });
    var tokenInput = target.querySelector('input[name="csrfmiddlewaretoken"]');
    var token = tokenCookie
      ? decodeURIComponent(tokenCookie.slice("csrftoken=".length))
      : tokenInput && tokenInput.value;
    if (token) {
      window.csrf_token = token;
      target.setAttribute(
        "hx-headers",
        JSON.stringify({ "X-CSRFToken": token }),
      );
    }
  }
  function mount() {
    var current = root();
    if (!current || !pendingMount) return;
    pendingMount = false;
    disposedTransition = false;
    if (pendingTitle) {
      document.title = pendingTitle;
      pendingTitle = null;
    }
    applyRootMetadata(current, current);
    if (window.htmx) window.htmx.process(current);
    initializers.splice(0).forEach(function (initialize) {
      initialize();
    });
    if (window.MediaViewerPlayer && current.querySelector("#b2-video"))
      window.MediaViewerPlayer.init();
    clearError();
    clearLoading();
    var heading = current.querySelector("h1");
    var focusTarget = current.querySelector("#page-content") || heading;
    if (focusTarget) {
      focusTarget.setAttribute("tabindex", "-1");
      focusTarget.focus({ preventScroll: true });
    }
    var status = document.getElementById("navigation-status");
    if (status)
      status.textContent = heading ? heading.textContent : document.title;
  }
  function installAjaxEpochGuard() {
    var $ = window.jQuery;
    if (!$ || window.__mediaViewerAjaxEpochGuard) return;
    window.__mediaViewerAjaxEpochGuard = true;
    $.ajaxPrefilter(function (options) {
      var requestEpoch = epoch;
      ["success", "error", "complete"].forEach(function (name) {
        var callback = options[name];
        if (typeof callback === "function")
          options[name] = function () {
            if (requestEpoch === epoch) return callback.apply(this, arguments);
          };
      });
    });
  }
  window.MediaViewerNavigation = {
    classify: classify,
    registerPageInit: function (callback) {
      if (typeof callback === "function") initializers.push(callback);
    },
  };
  installAjaxEpochGuard();
  document.addEventListener("htmx:beforeProcessNode", function (event) {
    var node = event.detail.elt;
    if (!node || !node.matches) return;
    if (node.matches("a[href]")) {
      if (
        classify("GET", node.href) &&
        !node.hasAttribute("download") &&
        !node.target
      ) {
        node.setAttribute("hx-boost", "true");
      } else node.setAttribute("hx-boost", "false");
    } else if (node.matches("form")) {
      if (node.getAttribute("hx-boost") === "false") return;
      var method = (node.method || "GET").toUpperCase();
      var action;
      try {
        action = new URL(
          node.action || window.location.href,
          window.location.href,
        );
      } catch (_) {
        node.setAttribute("hx-boost", "false");
        return;
      }
      var allowed = classify(method, action.href);
      if (method === "POST" && allowed && !node.target) {
        // Explicit verb keeps HTMX 2 from pushing a URL for its boosted POST forms.
        node.setAttribute("hx-post", action.href);
        node.setAttribute("hx-push-url", "false");
        node.setAttribute("hx-boost", "false");
      } else {
        node.setAttribute(
          "hx-boost",
          allowed && !node.target ? "true" : "false",
        );
      }
    }
  });
  document.addEventListener("htmx:validateUrl", function (event) {
    var method =
      event.detail.verb ||
      (event.detail.elt && event.detail.elt.method) ||
      "GET";
    if (classify(method, event.detail.url)) return;
    event.preventDefault();
  });
  document.addEventListener("htmx:beforeHistoryUpdate", function (event) {
    var method =
      event.detail.verb ||
      (event.detail.requestConfig && event.detail.requestConfig.verb);
    if (
      String(method || "").toUpperCase() === "POST" &&
      classify(
        "POST",
        event.detail.pathInfo && event.detail.pathInfo.requestPath,
      )
    ) {
      event.detail.history.type = null;
    }
  });
  document.addEventListener("htmx:beforeRequest", function (event) {
    if (event.detail.target && event.detail.target.id === "app-content") {
      cancelPendingHistoryRequest();
    }
    var current = root();
    if (!current) return;
    current.setAttribute("aria-busy", "true");
    var indicator = document.getElementById("navigation-indicator");
    if (indicator) indicator.hidden = false;
  });
  document.addEventListener("htmx:beforeSwap", function (event) {
    var detail = event.detail;
    if (!detail.target || detail.target.id !== "app-content") return;
    cancelPendingHistoryRequest();
    var status = detail.xhr.status;
    var incoming =
      status >= 200 && status < 300 && status !== 204 && detail.shouldSwap
        ? responseRoot(detail.xhr.responseText)
        : null;
    if (!incoming) {
      detail.shouldSwap = false;
      event.preventDefault();
      if (status !== 204)
        showError(
          status === 403
            ? "Your session cannot access this page. Reload and try again."
            : "Navigation failed. Your current page is unchanged.",
        );
      clearLoading();
      return;
    }
    dispose();
    detail.__mediaViewerIncomingRoot = incoming;
    pendingMount = true;
  });
  document.addEventListener("htmx:historyCacheMiss", function (event) {
    cancelPendingHistoryRequest();
    pendingHistoryRequest = {
      xhr: event.detail.xhr,
      historyElt: event.detail.historyElt,
      path: event.detail.path,
      cancelled: false,
    };
  });
  document.addEventListener("htmx:historyCacheMissLoad", function (event) {
    var detail = event.detail;
    var pending = pendingHistoryRequest;
    if (
      !pending ||
      pending.cancelled ||
      pending.xhr !== detail.xhr ||
      pending.historyElt !== detail.historyElt ||
      detail.historyElt !== root()
    ) {
      detail.swapSpec.swapStyle = "none";
      detail.response = "";
      detail.path = window.location.pathname + window.location.search;
      if (pending && pending.xhr === detail.xhr) pendingHistoryRequest = null;
      return;
    }
    pendingHistoryRequest = null;
    var incoming = responseRoot(detail.response);
    if (
      !incoming ||
      !detail.historyElt ||
      detail.historyElt.id !== "app-content"
    ) {
      detail.swapSpec.swapStyle = "none";
      showError(
        "Navigation returned an invalid page. Your current page is unchanged.",
      );
      clearLoading();
      window.location.assign(detail.path);
      return;
    }
    dispose();
    applyRootMetadata(detail.historyElt, incoming);
    pendingTitle = new DOMParser().parseFromString(
      detail.response,
      "text/html",
    ).title;
    detail.response = incoming.innerHTML;
    pendingMount = true;
  });
  document.addEventListener("htmx:historyCacheMissLoadError", function (event) {
    var pending = pendingHistoryRequest;
    if (
      !pending ||
      pending.cancelled ||
      pending.xhr !== event.detail.xhr ||
      pending.historyElt !== event.detail.historyElt ||
      event.detail.historyElt !== root()
    ) {
      if (pending && pending.xhr === event.detail.xhr)
        pendingHistoryRequest = null;
      return;
    }
    pendingHistoryRequest = null;
    window.location.assign(event.detail.path);
  });
  document.addEventListener("htmx:afterSettle", function (event) {
    var current = root();
    var target = event.detail.target;
    if (
      pendingMount &&
      current &&
      (target === current ||
        current.contains(target) ||
        current.contains(event.target))
    )
      mount();
  });
  document.addEventListener("htmx:afterRequest", function (event) {
    if (event.detail.failed) clearLoading();
  });
  document.addEventListener("htmx:sendError", function () {
    showError("Network error. Your current page is unchanged.");
    clearLoading();
  });
  document.addEventListener("htmx:timeout", function () {
    showError("Navigation timed out. Your current page is unchanged.");
    clearLoading();
  });
  if (document.readyState === "loading")
    document.addEventListener(
      "DOMContentLoaded",
      function () {
        pendingMount = true;
        mount();
      },
      { once: true },
    );
  else {
    pendingMount = true;
    mount();
  }
})(window, document);
