(function () {
  var REPO = 'techardentlabs/tallybook';
  var FALLBACK = 'https://github.com/' + REPO + '/releases/latest';
  var PATTERNS = {
    mac: /universal\.dmg$/i,
    'mac-any': /\.dmg$/i,
    win: /x64-setup\.exe$/i,
    'win-any': /-setup\.exe$/i,
    'win-msi': /\.msi$/i,
    'linux-appimage': /\.AppImage$/,
    'linux-deb': /\.deb$/,
    'linux-rpm': /\.rpm$/
  };
  function mb(n) { return (n / 1048576).toFixed(1) + ' MB'; }
  function pick(assets, key) {
    var a = assets.filter(function (x) { return PATTERNS[key].test(x.name) && !/\.sig$/.test(x.name); })[0];
    if (!a && key === 'mac') return pick(assets, 'mac-any');
    if (!a && key === 'win') return pick(assets, 'win-any');
    return a;
  }
  window.TallyBookRelease = fetch('https://api.github.com/repos/' + REPO + '/releases/latest')
    .then(function (r) { return r.ok ? r.json() : null; })
    .catch(function () { return null; })
    .then(function (rel) {
      if (!rel) return null;
      var assets = rel.assets || [];
      var out = { version: rel.tag_name.replace(/^v/, ''), date: (rel.published_at || '').slice(0, 10), files: {} };
      Object.keys(PATTERNS).forEach(function (k) { var a = pick(assets, k); if (a) out.files[k] = { url: a.browser_download_url, name: a.name, size: mb(a.size) }; });
      return out;
    });
  window.TallyBookRelease.then(function (rel) {
    document.querySelectorAll('[data-file]').forEach(function (el) {
      var f = rel && rel.files[el.getAttribute('data-file')];
      if (f) el.href = f.url; else el.href = FALLBACK;
    });
    document.querySelectorAll('[data-size]').forEach(function (el) {
      var f = rel && rel.files[el.getAttribute('data-size')];
      el.textContent = f ? f.size : '';
    });
    document.querySelectorAll('[data-fname]').forEach(function (el) {
      var f = rel && rel.files[el.getAttribute('data-fname')];
      el.textContent = f ? f.name : '';
    });
    document.querySelectorAll('[data-version]').forEach(function (el) { el.textContent = rel ? rel.version : 'latest'; });
    document.querySelectorAll('[data-date]').forEach(function (el) { el.textContent = rel && rel.date ? rel.date : ''; });
    var redirect = document.body.getAttribute('data-redirect');
    if (redirect) {
      var f = rel && rel.files[redirect];
      window.location.replace(f ? f.url : FALLBACK);
    }
    var ua = navigator.userAgent;
    var mobile = /Android|iPhone|iPad|iPod|Mobile/i.test(ua);
    var os = mobile ? 'win' : /Macintosh|Mac OS X/.test(ua) ? 'mac' : /Linux|X11|CrOS/.test(ua) ? 'linux-appimage' : 'win';
    var card = { mac: 'mac', win: 'windows', 'linux-appimage': 'linux' }[os];
    var el = document.getElementById(card);
    if (el && el.parentNode) { el.parentNode.insertBefore(el, el.parentNode.firstChild); el.style.borderColor = 'var(--sel)'; el.style.borderWidth = '2px'; }
    var label = { mac: 'for macOS', win: 'for Windows', 'linux-appimage': 'for Linux' };
    document.querySelectorAll('[data-auto]').forEach(function (el) {
      var f = rel && rel.files[os];
      var s = el.querySelector('small');
      if (s) s.textContent = label[os] + (f ? ' · ' + f.size : '');
      el.href = f ? f.url : '/download/' + card + '/';
    });
  });
})();
