/* ── Verification system with session auth ── */
var __verifySession=null; /* session token — authenticate once, use for all actions */

function toggleSqlEvidence(btn){
  var wrap=btn.nextElementSibling;
  wrap.style.display=wrap.style.display==='none'?'block':'none';
}
function copySqlEvidence(btn){
  var pre=btn.nextElementSibling;
  var text=pre.textContent;
  navigator.clipboard.writeText(text).then(function(){
    btn.textContent='Copied!';
    setTimeout(function(){btn.innerHTML='&#128203; Copy SQL';},1500);
  });
}

function _ensureAuth(){
  /* Returns a promise that resolves with auth params (session_token or password) */
  if(__verifySession) return Promise.resolve({session_token:__verifySession});
  var pwd=prompt('Enter verification password (authenticates for this session):');
  if(!pwd) return Promise.resolve(null);
  /* Try session auth first */
  return fetch(window.__apiBase+'/api/verify',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:'auth',password:pwd})
  }).then(function(r){return r.json()}).then(function(d){
    if(d.session_token){
      __verifySession=d.session_token;
      return {session_token:d.session_token};
    }
    /* Fallback: use password directly */
    return {password:pwd};
  }).catch(function(){
    return {password:pwd};
  });
}

function verifyFinding(findingId,action){
  var verifiedBy=null,note=null;
  if(action==='verify'){
    verifiedBy=prompt('Who from Commercial Finance validated this?');
    if(!verifiedBy)return;
    note=prompt('Add a note (optional):');
  }
  _ensureAuth().then(function(auth){
    if(!auth)return;
    var dt=document.documentElement.getAttribute('data-generated-utc');
    var dateStr=dt?dt.split('T')[0]:'unknown';
    var payload=Object.assign({finding_id:findingId,action:action,date:dateStr},auth);
    if(verifiedBy)payload.verified_by=verifiedBy;
    if(note)payload.note=note;
    fetch(window.__apiBase+'/api/verify',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    }).then(function(r){return r.json()}).then(function(d){
      if(d.error){__verifySession=null;alert('Error: '+d.error);return;}
      applyVerificationState(findingId,action,verifiedBy,note);
    }).catch(function(e){alert('Verification failed: '+e);});
  });
}

function revertFinding(findingId){
  _ensureAuth().then(function(auth){
    if(!auth)return;
    var dt=document.documentElement.getAttribute('data-generated-utc');
    var dateStr=dt?dt.split('T')[0]:'unknown';
    var payload=Object.assign({finding_id:findingId,action:'revert',date:dateStr},auth);
    fetch(window.__apiBase+'/api/verify',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    }).then(function(r){return r.json()}).then(function(d){
      if(d.error){__verifySession=null;alert('Error: '+d.error);return;}
      location.reload();
    }).catch(function(e){alert('Revert failed: '+e);});
  });
}

function applyVerificationState(findingId,action,verifiedBy,note){
  var els=document.querySelectorAll('[data-finding-id="'+findingId+'"]');
  var h3=null;
  els.forEach(function(el){
    if(el.tagName==='H3'){h3=el;}
  });
  var tipExtra='';
  if(verifiedBy)tipExtra+=' Confirmed by '+verifiedBy+'.';
  if(note)tipExtra+=' Note: '+note;
  var nameLabel=verifiedBy?(' &amp; '+verifiedBy):'';
  if(action==='verify'){
    els.forEach(function(el){
      if(el.classList.contains('verify-pill-contested')||el.classList.contains('verify-pill-agreed')){
        el.className='verify-pill verify-pill-agreed';
        el.innerHTML='&#10003; VERIFIED<span class="verify-tip">Verified by OpenAI, Claude'+nameLabel+'.'+tipExtra+'</span>';
      }
      if(el.classList.contains('verify-contested-detail')){
        el.style.display='none';
      }
    });
    /* Add revert link after the pill */
    var pill=h3?h3.parentElement.querySelector('.verify-pill-agreed[data-finding-id="'+findingId+'"]'):null;
    if(pill&&!pill.nextElementSibling||pill&&!pill.nextElementSibling.classList.contains('verify-revert')){
      var rv=document.createElement('a');
      rv.href='#';rv.className='verify-revert';
      rv.textContent='revert';
      rv.onclick=function(e){e.preventDefault();revertFinding(findingId);};
      pill.parentNode.insertBefore(rv,pill.nextSibling);
    }
  }else if(action==='remove'){
    var driverName='';
    if(h3){
      driverName=h3.textContent.replace(/VERIFIED|DISPUTED|REVIEW|UNVERIFIED|REMOVED|Trend/g,'').trim().toLowerCase();
      h3.style.opacity='0.2';
      var sib=h3.nextElementSibling;
      while(sib&&sib.tagName!=='H3'&&sib.tagName!=='H2'){
        sib.style.opacity='0.2';
        sib.style.pointerEvents='none';
        sib=sib.nextElementSibling;
      }
    }
    els.forEach(function(el){
      if(el.classList.contains('verify-pill-contested')){
        el.className='verify-pill verify-pill-unverified';
        el.innerHTML='&#10007; REMOVED';
        el.style.opacity='1';
      }
    });
    /* Add revert link */
    if(h3){
      var rv=document.createElement('a');
      rv.href='#';rv.className='verify-revert';rv.style.opacity='1';
      rv.textContent='revert';
      rv.onclick=function(e){e.preventDefault();revertFinding(findingId);};
      h3.appendChild(rv);
    }
    /* Fade matching At a Glance bullet */
    if(driverName){
      var glance=document.getElementById('section-at-a-glance');
      if(glance){
        var lis=glance.querySelectorAll('li');
        lis.forEach(function(li){
          var txt=li.textContent.toLowerCase();
          var words=driverName.split(/[\s\-\u2014]+/).filter(function(w){return w.length>3;});
          var matches=words.filter(function(w){return txt.indexOf(w)!==-1;});
          if(matches.length>=2){
            li.style.opacity='0.2';
            li.style.textDecoration='line-through';
          }
        });
      }
    }
  }
}

/* Load verification overrides from KV on page load */
(function(){
  var dt=document.documentElement.getAttribute('data-generated-utc');
  if(!dt)return;
  var dateStr=dt.split('T')[0];
  fetch(window.__apiBase+'/api/verify?date='+dateStr)
    .then(function(r){if(r.ok)return r.json();return {}})
    .then(function(overrides){
      if(!overrides||!overrides.findings)return;
      Object.keys(overrides.findings).forEach(function(fid){
        var f=overrides.findings[fid];
        applyVerificationState(fid,f.action,f.verified_by,f.note);
      });
    }).catch(function(){});
})();
