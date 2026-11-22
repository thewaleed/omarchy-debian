// OSC 52 clipboard bridge for the browser Herdr terminal (term.thewaleed.me).
//
// herdr copies a mouse/copy-mode selection by sending OSC 52 (ESC ] 52 ; c ; <base64> BEL)
// to the terminal it runs in. ttyd's bundled xterm.js has no OSC 52 handler, so in the
// browser the copy was silently dropped, and pasting into another pane had nothing to paste.
// build-ttyd-index injects this file into ttyd's stock page; ttyd exposes its xterm.js
// Terminal as window.term.
(function () {
  "use strict";

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* nothing else to try */ }
    ta.remove();
    if (window.term) window.term.focus();
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(function () { fallbackCopy(text); });
    } else {
      fallbackCopy(text);
    }
  }

  function decodeBase64Utf8(b64) {
    var bin = atob(b64);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder("utf-8").decode(bytes);
  }

  // data is "<targets>;<payload>". A payload of "?" is a clipboard read request,
  // which is not answered: a remote program must not be able to read this
  // machine's clipboard.
  function onOsc52(data) {
    var sep = data.indexOf(";");
    if (sep < 0) return true;
    var payload = data.slice(sep + 1);
    if (payload === "" || payload === "?") return true;
    try { copy(decodeBase64Utf8(payload)); } catch (e) { /* bad base64: ignore */ }
    return true;
  }

  // window.term appears once ttyd's app has mounted. Re-check periodically so a
  // new Terminal (if ttyd ever recreates it) also gets the handler.
  var hooked = null;
  function hook() {
    var t = window.term;
    if (t && t !== hooked && t.parser) {
      t.parser.registerOscHandler(52, onOsc52);
      hooked = t;
    }
  }
  hook();
  setInterval(hook, 1000);
})();
