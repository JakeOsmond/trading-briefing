/* Context Manager — standalone JS (no f-string escaping needed) */
var __apiBase = location.hostname.includes('staging') ? 'https://trading-covered.pages.dev' : '';
var __cmSession = null;
var __addCounter = 0;

function _ensureAuth() {
  if (__cmSession) return Promise.resolve({session_token: __cmSession});
  var pwd = prompt('Enter verification password:');
  if (!pwd) return Promise.resolve(null);
  return fetch(__apiBase + '/api/verify', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action: 'auth', password: pwd})
  }).then(function(r) { return r.json() }).then(function(d) {
    if (d.session_token) { __cmSession = d.session_token; return {session_token: d.session_token}; }
    return {password: pwd};
  }).catch(function() { return {password: pwd}; });
}

function cmPreview(fileId) {
  var el = document.getElementById(fileId);
  if (!el) return;
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
  if (el.style.display === 'block') el.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function cmRemove(filedTo, filedText, elId) {
  _ensureAuth().then(function(auth) {
    if (!auth) return;
    var payload = Object.assign({
      finding_id: 'context:' + elId,
      action: 'remove_context',
      date: new Date().toISOString().split('T')[0],
      note: JSON.stringify({filed_to: filedTo, filed_text: filedText})
    }, auth);
    fetch(__apiBase + '/api/verify', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    }).then(function(r) { return r.json() }).then(function(d) {
      if (d.error) { alert('Error: ' + d.error); return; }
      var el = document.getElementById(elId);
      if (el) el.style.display = 'none';
      try {
        var removed = JSON.parse(localStorage.getItem('cm_removed') || '[]');
        removed.push(filedText.substring(0, 50));
        localStorage.setItem('cm_removed', JSON.stringify(removed));
      } catch(e) {}
    }).catch(function(e) { alert('Remove failed: ' + e); });
  });
}

function cmRemoveManual(addId, elId) {
  var pwd = prompt('Enter verification password to remove:');
  if (!pwd) return;
  fetch(__apiBase + '/api/verify', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      finding_id: addId,
      action: 'delete_pending_add',
      date: new Date().toISOString().split('T')[0],
      password: pwd
    })
  }).then(function(r) { return r.json() }).then(function(d) {
    if (d.error) { alert('Error: ' + d.error); return; }
    var card = document.querySelector('[data-add-id="' + addId + '"]');
    if (card) card.remove();
    else {
      var el = document.getElementById(elId);
      if (el) { var parent = el.closest('.cm-file'); if (parent) parent.remove(); else el.remove(); }
    }
    try {
      var pending = JSON.parse(localStorage.getItem('cm_pending_adds') || '[]');
      pending = pending.filter(function(p) { return p.id !== addId; });
      localStorage.setItem('cm_pending_adds', JSON.stringify(pending));
    } catch(e) {}
    try {
      var removed = JSON.parse(localStorage.getItem('cm_removed_pending') || '[]');
      removed.push(addId);
      localStorage.setItem('cm_removed_pending', JSON.stringify(removed));
    } catch(e) {}
  }).catch(function(e) { alert('Remove failed: ' + e); });
}

function _showPendingAdd(addId, text, name) {
  __addCounter++;
  var itemId = 'cm-manual-' + __addCounter;
  var safeText = text.split('&').join('&amp;').split('<').join('&lt;').split('>').join('&gt;');
  var safeName = (name || 'user').split('&').join('&amp;').split('<').join('&lt;');
  var itemHtml = '<div class="cm-ai-item" id="' + itemId + '">'
    + '<span class="cm-ai-text">' + safeText
    + ' <em style="opacity:0.5">(pending — added by ' + safeName + ')</em></span>'
    + '<button class="cm-remove-btn" onclick="cmRemoveManual(&quot;' + addId + '&quot;,&quot;' + itemId + '&quot;)">✕ Remove</button>'
    + '</div>';
  var addSection = document.querySelector('.cm-add-section');
  addSection.insertAdjacentHTML('beforebegin',
    '<div class="cm-file cm-pending-card" data-add-id="' + addId + '" style="border-color:rgba(0,176,166,0.3)"><div class="cm-file-header">'
    + '<span class="cm-file-icon">✨</span> <span class="cm-file-name">Added by ' + safeName + '</span>'
    + '<span class="cm-file-meta">pending next run</span></div>' + itemHtml + '</div>');
}

function cmAddContext() {
  var text = document.getElementById('cmAddText').value.trim();
  var name = document.getElementById('cmAddName').value.trim();
  var pwd = document.getElementById('cmAddPassword').value;
  if (!text) { alert('Please enter some context'); return; }
  if (!name) { alert('Please enter your name'); return; }
  if (!pwd) { alert('Password required'); return; }
  var addId = 'manual-' + Date.now();
  document.querySelector('.cm-add-btn').textContent = 'Adding...';
  fetch(__apiBase + '/api/verify', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      finding_id: addId,
      action: 'add_context',
      date: new Date().toISOString().split('T')[0],
      password: pwd,
      verified_by: name,
      note: text
    })
  }).then(function(r) { return r.json() }).then(function(d) {
    document.querySelector('.cm-add-btn').textContent = 'Add Context';
    if (d.error) { alert('Error: ' + d.error); return; }
    try {
      var pending = JSON.parse(localStorage.getItem('cm_pending_adds') || '[]');
      pending.push({id: addId, text: text, name: name, time: new Date().toISOString()});
      localStorage.setItem('cm_pending_adds', JSON.stringify(pending));
    } catch(e) {}
    _showPendingAdd(addId, text, name);
    document.getElementById('cmAddText').value = '';
    document.getElementById('cmAddPassword').value = '';
  }).catch(function(e) {
    document.querySelector('.cm-add-btn').textContent = 'Add Context';
    alert('Failed: ' + e);
  });
}

/* On page load: fetch pending state from KV, apply removals, show pending adds */
(function initContextState() {
  fetch(__apiBase + '/api/verify?type=pending_context')
    .then(function(r) { return r.json() })
    .then(function(d) {
      /* 1. Hide items that have pending removals in KV */
      var removals = d.pending_removals || [];
      removals.forEach(function(r) {
        var info = r.filed_info || {};
        var text = (info.filed_text || '').trim();
        if (!text) return;
        document.querySelectorAll('.cm-ai-item').forEach(function(el) {
          if (el.textContent.indexOf(text.substring(0, 50)) !== -1) el.style.display = 'none';
        });
      });

      /* 2. Show pending adds from KV (skip removed ones) */
      var adds = d.pending_adds || [];
      var removedPending = [];
      try { removedPending = JSON.parse(localStorage.getItem('cm_removed_pending') || '[]'); } catch(e) {}
      var addSection = document.querySelector('.cm-add-section');
      if (addSection && adds.length) {
        adds.forEach(function(item) {
          var addId = item.id || ('pending-' + Math.random());
          if (removedPending.indexOf(addId) !== -1) return;
          _showPendingAdd(addId, item.raw_text || '', item.added_by || 'user');
        });
      }
    })
    .catch(function() {});

  /* 3. Restore pending adds from localStorage */
  try {
    var local = JSON.parse(localStorage.getItem('cm_pending_adds') || '[]');
    local.forEach(function(item) {
      if (!document.querySelector('[data-add-id="' + item.id + '"]')) {
        _showPendingAdd(item.id, item.text, item.name);
      }
    });
  } catch(e) {}

  /* 4. Hide items removed via localStorage */
  try {
    var removed = JSON.parse(localStorage.getItem('cm_removed') || '[]');
    if (removed.length) {
      document.querySelectorAll('.cm-ai-item').forEach(function(el) {
        var txt = el.textContent;
        removed.forEach(function(r) { if (txt.indexOf(r) !== -1) el.style.display = 'none'; });
      });
    }
  } catch(e) {}
})();
