/* Imita o motor CEP da Adobe para o plugin Fluxogama rodar fora do Illustrator.
   As chamadas vão para o servidor da Suíte (fluxogama.py), que fala com o Illustre - Angerô. */
(function () {
  function postSync(rota, dados) {
    var x = new XMLHttpRequest();
    x.open("POST", rota, false); // o cep.fs original é síncrono
    x.setRequestHeader("Content-Type", "application/json");
    x.setRequestHeader("X-Cep", "1");
    x.send(JSON.stringify(dados));
    return JSON.parse(x.responseText);
  }
  function getSync(rota) {
    var x = new XMLHttpRequest();
    x.open("GET", rota, false);
    x.send();
    return x.responseText;
  }

  window.__adobe_cep__ = {
    getExtensionId: function () { return "br.com.fluxogama.extension"; },
    getSystemPath: function (tipo) { return getSync("/cep/caminho?tipo=" + encodeURIComponent(tipo)); },
    getHostEnvironment: function () {
      return JSON.stringify({ appName: "ILST", appVersion: "29.0", appLocale: "pt_BR", appUILocale: "pt_BR",
        appId: "ILST", isAppOnline: true, appSkinInfo: { baseFontFamily: "Segoe UI", baseFontSize: 12,
        appBarBackgroundColor: { color: { red: 50, green: 50, blue: 50, alpha: 255 } },
        panelBackgroundColor: { color: { red: 50, green: 50, blue: 50, alpha: 255 } } } });
    },
    getCurrentApiVersion: function () { return JSON.stringify({ major: 9, minor: 4, micro: 0 }); },
    evalScript: function (script, callback) {
      fetch("/cep/eval", { method: "POST", headers: { "Content-Type": "application/json", "X-Cep": "1" },
                           body: JSON.stringify({ script: script }) })
        .then(function (r) { return r.json(); })
        .then(function (j) { if (typeof callback === "function") callback(j.resultado); })
        .catch(function () { if (typeof callback === "function") callback("EvalScript error."); });
    },
    getScaleFactor: function () { return 1; },
    getMonitorScaleFactor: function () { return 1; },
    getNetworkPreferences: function () { return "{}"; },
    getHostCapabilities: function () { return "{}"; },
    getExtensions: function () { return "[]"; },
    invokeSync: function () { return ""; },
    invokeAsync: function () {},
    addEventListener: function () {},
    removeEventListener: function () {},
    dispatchEvent: function () {},
    closeExtension: function () { window.close(); },
    requestOpenExtension: function () {},
    resizeContent: function () {},
    registerKeyEventsInterest: function () {},
    registerInvalidCertificateCallback: function () {},
    setScaleFactorChangedHandler: function () {},
    initResourceBundle: function () { return "{}"; },
    dumpInstallationInfo: function () { return ""; },
    loadSnapshot: function () {}
  };

  function stat(caminho) {
    var r = postSync("/cep/fs", { op: "stat", caminho: caminho });
    if (r.err === 0) {
      var d = r.data;
      r.data = { mtime: new Date(d.mtime), isFile: function () { return d.isFile; },
                 isDirectory: function () { return d.isDirectory; } };
    }
    return r;
  }

  window.cep = {
    encoding: { UTF8: "UTF-8", Base64: "Base64" },
    fs: {
      NO_ERROR: 0, ERR_UNKNOWN: 1, ERR_INVALID_PARAMS: 2, ERR_NOT_FOUND: 3, ERR_CANT_READ: 4,
      ERR_UNSUPPORTED_ENCODING: 5, ERR_CANT_WRITE: 6, ERR_OUT_OF_SPACE: 7, ERR_NOT_FILE: 8,
      ERR_NOT_DIRECTORY: 9, ERR_FILE_EXISTS: 10,
      stat: stat,
      readFile: function (c, cod) { return postSync("/cep/fs", { op: "readFile", caminho: c, codificacao: cod || "UTF-8" }); },
      writeFile: function (c, dados, cod) { return postSync("/cep/fs", { op: "writeFile", caminho: c, dados: dados, codificacao: cod || "UTF-8" }); },
      makedir: function (c) { return postSync("/cep/fs", { op: "makedir", caminho: c }); },
      deleteFile: function (c) { return postSync("/cep/fs", { op: "deleteFile", caminho: c }); }
    },
    util: {
      openURLInDefaultBrowser: function (url) { postSync("/cep/abrir-url", { url: url }); return { err: 0 }; }
    }
  };
})();
