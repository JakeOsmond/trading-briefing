/* ── Staging: route API calls to production (preview deployments have no secrets) ── */
window.__apiBase=location.hostname.includes('staging')?'https://trading-covered.pages.dev':'';

/* ── Pre-loaded driver trend data (keyed by driver name) ── */
window.__driverTrends=__DRIVER_TRENDS_JSON__;

/* ── Pre-computed field values for AI chat (from pipeline) ── */
window.__fieldDiscovery=__FIELD_DISCOVERY_JSON__;

/* ── Chart ── */
const data=__CHART_DATA_JSON__;
const chart=document.getElementById('trendChart');
let chartBuilt=false;

function buildChart(){
  if(chartBuilt||!data.length) return;
  chartBuilt=true;
  const maxGP=Math.max(...data.map(d=>d.gp));
  const minGP=Math.min(...data.map(d=>d.gp));
  const range=maxGP-minGP||1;
  const avgGP=data.reduce((s,d)=>s+d.gp,0)/data.length;
  const avgH=((avgGP-minGP)/range)*150+20;
  const dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  data.forEach((d,i)=>{
    const col=document.createElement('div');col.className='bar-col';
    const h=((d.gp-minGP)/range)*150+20;
    /* Green = YoY growth (GP > LY), Red = YoY decline */
    const isGrowth=d.ly_gp>0?d.gp>=d.ly_gp:true;
    const gradTop=isGrowth?'#00D4C8':'#FF8A91';
    const gradBot=isGrowth?'#00B0A6':'#FF5F68';
    const dateObj=new Date(d.date+'T00:00:00');
    const dateLabel=dayNames[dateObj.getDay()]+' '+dateObj.getDate();
    const fullDate=dayNames[dateObj.getDay()]+' '+dateObj.getDate()+' '+monthNames[dateObj.getMonth()];
    /* YoY tooltip values */
    const yoyPct=d.yoy_pct!==null?d.yoy_pct:null;
    const yoyAbs=d.yoy_abs!==null?d.yoy_abs:null;
    const yoyClass=yoyPct!==null?(yoyPct>=0?'tt-yoy-up':'tt-yoy-down'):'tt-val';
    const yoySign=yoyPct!==null&&yoyPct>=0?'+':'';
    const yoyAbsSign=yoyAbs!==null&&yoyAbs>=0?'+':'';
    col.innerHTML=`
      <div class="tooltip">
        <div class="tt-date">${fullDate}</div>
        <div class="tt-row">TY GP: <span class="tt-val" style="color:${gradTop}">&pound;${d.gp.toLocaleString()}</span></div>
        <div class="tt-row">LY GP: <span class="tt-val">&pound;${d.ly_gp?d.ly_gp.toLocaleString():'N/A'}</span></div>
        ${yoyPct!==null?`<div class="tt-row">YoY: <span class="${yoyClass}">${yoyAbsSign}&pound;${yoyAbs.toLocaleString()} (${yoySign}${yoyPct}%)</span></div>`:''}
        <div class="tt-row">Policies TY: <span class="tt-val">${d.policies.toLocaleString()}</span></div>
      </div>
      <div class="bar animate-in" style="height:${h}px;background:linear-gradient(to top,${gradBot},${gradTop});animation-delay:${i*60}ms;transform:scaleY(0)"></div>
      <div class="bar-label">${dateLabel}</div>`;
    chart.appendChild(col);
  });

  /* Average line */
  const avgLine=document.createElement('div');
  avgLine.className='avg-line';
  avgLine.style.bottom=avgH+'px';
  avgLine.innerHTML='<div class="avg-line-inner"></div>';
  chart.appendChild(avgLine);
  requestAnimationFrame(()=>{
    requestAnimationFrame(()=>{avgLine.classList.add('animate-in')});
  });

}

/* ── SQL dig toggle/copy ── */
function toggleSQL(id){
  const el=document.getElementById(id);
  if(el.style.display==='none'){
    el.style.display='block';
    /* Basic SQL keyword highlighting */
    const code=el.querySelector('code');
    if(code&&!code.dataset.highlighted){
      code.dataset.highlighted='1';
      const keywords=/\b(SELECT|FROM|WHERE|AND|OR|GROUP BY|ORDER BY|JOIN|LEFT|RIGHT|INNER|ON|AS|IN|NOT|NULL|IS|BETWEEN|LIKE|LIMIT|OFFSET|HAVING|UNION|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TABLE|INTO|VALUES|SET|CASE|WHEN|THEN|ELSE|END|COUNT|SUM|AVG|MIN|MAX|DISTINCT|WITH|OVER|PARTITION BY|ROW_NUMBER|RANK|DENSE_RANK|COALESCE|CAST|EXTRACT|DATE|TIMESTAMP|INTERVAL|TRUE|FALSE|ASC|DESC|EXISTS|ANY|ALL|EXCEPT|INTERSECT|CROSS|FULL|OUTER|NATURAL|USING|RECURSIVE|LATERAL|WINDOW|FILTER|WITHIN|ARRAY_AGG|STRING_AGG|UNNEST|STRUCT|SAFE_DIVIDE|IF|IFNULL|NULLIF|FORMAT_DATE|DATE_DIFF|DATE_ADD|DATE_SUB|DATE_TRUNC|PARSE_DATE|CURRENT_DATE|CURRENT_TIMESTAMP|GENERATE_DATE_ARRAY|LAG|LEAD)\b/gi;
      const strings=/'([^']*)'/g;
      let html=code.innerHTML;
      html=html.replace(strings,`<span class="str">'$1'</span>`);
      html=html.replace(keywords,(m)=>'<span class="kw">'+m+'</span>');
      code.innerHTML=html;
    }
  }else{
    el.style.display='none';
  }
}
function copySQL(id){
  const el=document.getElementById(id);
  const sql=el.querySelector('code').innerText;
  navigator.clipboard.writeText(sql).then(()=>{
    const btn=el.querySelector('.copy-btn');
    btn.textContent='Copied!';
    setTimeout(()=>btn.textContent='Copy',2000);
  });
}

/* ── Ask about this driver ── */
/* ── Animated AI loading stepper ── */
const AI_STEPS_INITIAL=[
  'Connecting to BigQuery…',
  'Checking today\'s date…',
  'Writing SQL query…',
  'Running query against BigQuery…',
  'Analysing results…',
  'Running follow-up query…',
  'Cross-referencing data…',
  'Verifying figures…',
  'Checking year-on-year comparisons…',
  'Building the narrative…',
  'Nearly there — refining the answer…',
  'Formatting answer…'
];
const AI_STEPS_SLOW=[
  'Taking longer than usual — still working on it…',
  'Still crunching the numbers — complex query running…',
  'Hang tight — pulling additional data…',
  'Still processing — cross-referencing results…',
  'Working through a deeper analysis…',
  'Still going — validating the figures…',
  'Wrapping up the analysis…',
  'Running final checks on the data…',
  'Almost done — formatting the response…'
];
const AI_STEP_FINAL='Preparing your answer…';

function createAILoadingEl(){
  const container=document.createElement('div');
  container.className='ai-loading-steps';
  return container;
}

function startAILoadingStepper(container){
  let stepIdx=0;
  let phase='initial';
  let slowIdx=0;
  const MAX_VISIBLE=4;
  const startTime=Date.now();

  function addStep(text){
    if(container._stopped) return;
    const prev=container.querySelector('.ai-step.active');
    if(prev){prev.classList.remove('active');prev.classList.add('done');}
    const steps=container.querySelectorAll('.ai-step');
    if(steps.length>=MAX_VISIBLE){
      const oldest=steps[0];
      oldest.style.opacity='0';
      oldest.style.transform='translateY(-10px)';
      oldest.style.maxHeight='0';
      oldest.style.marginBottom='0';
      oldest.style.paddingTop='0';
      oldest.style.paddingBottom='0';
      oldest.style.transition='all 0.3s ease';
      setTimeout(()=>oldest.remove(),300);
    }
    const step=document.createElement('div');
    step.className='ai-step';
    step.innerHTML='<span class="ai-step-dot"></span><span>'+text+'</span>';
    container.appendChild(step);
    requestAnimationFrame(()=>requestAnimationFrame(()=>step.classList.add('active')));
    const scrollParent=container.closest('.chat-messages')||container.closest('.ask-response');
    if(scrollParent) scrollParent.scrollTop=scrollParent.scrollHeight;
  }

  function tick(){
    if(container._stopped) return;
    const elapsed=Date.now()-startTime;
    if(phase==='initial'){
      if(stepIdx<AI_STEPS_INITIAL.length){
        addStep(AI_STEPS_INITIAL[stepIdx]);
        stepIdx++;
        if(elapsed>=180000){ phase='slow'; container._timer=setTimeout(tick,4000); return; }
        const timings=[2000,4000,8000,12000,14000,16000,18000,20000,20000,20000,18000,16000];
        container._timer=setTimeout(tick,timings[Math.min(stepIdx-1,timings.length-1)]);
      } else {
        if(elapsed>=180000){ phase='slow'; container._timer=setTimeout(tick,4000); }
        else { container._timer=setTimeout(tick,6000); }
      }
    } else if(phase==='slow'){
      if(slowIdx<AI_STEPS_SLOW.length){
        addStep(AI_STEPS_SLOW[slowIdx]);
        slowIdx++;
        container._timer=setTimeout(tick,20000);
      } else {
        phase='final';
        addStep(AI_STEP_FINAL);
      }
    }
  }

  tick();
  return container;
}

function stopAILoadingStepper(container){
  container._stopped=true;
  if(container._timer) clearTimeout(container._timer);
  const active=container.querySelector('.ai-step.active');
  if(active){active.classList.remove('active');active.classList.add('done');}
}

/* ── Fuzzy-match heading text to best driver trend key ── */
const __trendUsed=new Set();
function _matchTrend(headingText){
  const trends=window.__driverTrends||{};
  const keys=Object.keys(trends);
  if(!keys.length) return null;
  const stop=new Set(['the','a','an','and','or','of','in','on','to','for','is','from','by','with','not','recurring','emerging','new','trend']);
  function tokens(s){
    return s.toLowerCase().replace(/[^a-z0-9\s/]/g,' ').split(/\s+/)
      .flatMap(w=>w.split('/')).filter(w=>w.length>1&&!stop.has(w));
  }
  const hTokens=new Set(tokens(headingText));
  let bestKey=null,bestScore=0;
  for(const key of keys){
    if(__trendUsed.has(key)) continue;
    const kTokens=new Set(tokens(key));
    let overlap=0;
    for(const t of hTokens) if(kTokens.has(t)) overlap++;
    const score=overlap/Math.min(hTokens.size,kTokens.size);
    if(score>bestScore&&overlap>=1){bestScore=score;bestKey=key;}
  }
  if(bestKey&&bestScore>=0.25){
    __trendUsed.add(bestKey);
    return trends[bestKey];
  }
  return null;
}

/* ── Toggle matched trend chart (pre-loaded, instant) ── */
function toggleMatchedTrend(trendId, btn){
  const container=document.getElementById(trendId);
  if(!container) return;

  /* Toggle off */
  if(container.querySelector('.yoy-trend-wrap')){
    container.innerHTML='';
    return;
  }

  /* Get heading text and match to trend data */
  const h3=btn.closest('h3');
  const heading=h3?h3.textContent.replace(/Trend.*/,'').replace(/Recovery/g,'').trim():'Driver';
  let data=container._matchedData;
  if(!data){
    data=_matchTrend(heading);
    container._matchedData=data;
  }
  if(!data){
    /* Fallback to live API fetch */
    fetchDriverTrend(trendId,btn);
    return;
  }
  try{
    const trendResult={ty:data.ty.map(d=>({dt:d.dt,gp:d.val,vol:0})),ly:data.ly.map(d=>({dt:d.dt,gp:d.val,vol:0}))};
    renderYoYTrend(container, trendResult, heading, data);
    /* Update button with persistence info */
    const cd=data.consistent_days||0;
    const td=data.total_days||10;
    btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>Trend ('+cd+'/'+td+'d)';
    /* Insert recovery badge if applicable */
    if(data.recovery&&h3&&!h3.querySelector('.badge-recovery')){
      const badge=document.createElement('span');
      badge.className='badge-recovery';
      badge.textContent='Recovery';
      const trendBtn=h3.querySelector('.view-trend-btn');
      if(trendBtn) h3.insertBefore(badge,trendBtn);
    }
  }catch(e){
    container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">Error: '+e.message+'</div>';
  }
}

/* ── Fetch and render YoY trend bar chart for recurring/emerging drivers ── */
function fetchDriverTrend(trendId, btn){
  const container=document.getElementById(trendId);
  if(!container) return;

  /* Toggle: if already shown, hide */
  if(container.querySelector('.yoy-trend-wrap')&&!container.querySelector('.loading')){
    container.innerHTML='';
    btn.textContent='Trend';
    return;
  }

  /* Get driver context from heading */
  const h3=btn.closest('h3');
  const headingText=h3?h3.textContent.replace('Trend','').trim():'';

  /* Build dates: 14 days ending yesterday */
  const now=new Date();
  const yesterday=new Date(now);yesterday.setDate(now.getDate()-1);
  const start=new Date(yesterday);start.setDate(yesterday.getDate()-13);
  const lyEnd=new Date(yesterday);lyEnd.setDate(yesterday.getDate()-364);
  const lyStart=new Date(start);lyStart.setDate(start.getDate()-364);

  function fmt(d){return d.toISOString().slice(0,10)}

  /* Ask AI to write the segment filter SQL for this driver */
  container.innerHTML='<div class="yoy-trend-wrap loading">Loading trend data…</div>';
  btn.textContent='Loading…';

  /* Use the ask endpoint to get the AI to write + run a trend query */
  fetch((window.__apiBase||'')+'/api/ask',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      question:'Return ONLY a JSON object with a single key "segment_filter" containing a SQL WHERE clause fragment that isolates this segment: "'+headingText+'". Examples: "distribution_channel=\'Direct\' AND policy_type=\'Single\'", "cover_level_name=\'Bronze\'". Return ONLY valid JSON, no explanation.',
      mode:'general'
    })
  })
  .then(r=>r.json())
  .then(data=>{
    /* Try to extract segment_filter from the AI response */
    let segFilter='1=1';
    try{
      const answer=data.answer||'';
      const jsonMatch=answer.match(/\{[^{}]*"segment_filter"[^{}]*\}/);
      if(jsonMatch){
        segFilter=JSON.parse(jsonMatch[0]).segment_filter||'1=1';
      }else{
        /* Try to find a WHERE clause fragment */
        const whereMatch=answer.match(/(?:distribution_channel|policy_type|cover_level_name|insurance_group)[^"\n]{5,120}/i);
        if(whereMatch) segFilter=whereMatch[0].replace(/[`]/g,"'");
      }
    }catch(e){}

    /* Now run the actual trend queries */
    const tySQL=`SELECT transaction_date AS dt, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS vol FROM \`hx-data-production.commercial_finance.insurance_policies_new\` WHERE transaction_date BETWEEN '${fmt(start)}' AND '${fmt(yesterday)}' AND ${segFilter} GROUP BY transaction_date ORDER BY transaction_date`;
    const lySQL=`SELECT transaction_date AS dt, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS vol FROM \`hx-data-production.commercial_finance.insurance_policies_new\` WHERE transaction_date BETWEEN '${fmt(lyStart)}' AND '${fmt(lyEnd)}' AND ${segFilter} GROUP BY transaction_date ORDER BY transaction_date`;

    return fetch((window.__apiBase||'')+'/api/ask',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        mode:'trend',
        trend_sql:{ty:tySQL,ly:lySQL}
      })
    });
  })
  .then(r=>r.json())
  .then(result=>{
    if(result.error){
      container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">Could not load trend: '+result.error+'</div>';
      btn.textContent='Trend';
      return;
    }
    renderYoYTrend(container, result.trend, headingText, null);
    btn.textContent='Hide trend';
  })
  .catch(err=>{
    container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">Error: '+err.message+'</div>';
    btn.textContent='Trend';
  });
}

function renderYoYTrend(container, trendData, title, meta){
  const tyRows=trendData.ty||[];
  const lyRows=trendData.ly||[];
  if(!tyRows.length){
    container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">No data returned.</div>';
    return;
  }

  /* Compute persistence from the data if not provided */
  const direction=(meta&&meta.direction)||'down';
  let consistentDays=meta&&meta.consistent_days;
  let totalDays=meta&&meta.total_days;
  let persistenceLabel=meta&&meta.persistence;

  if(consistentDays==null){
    const n=Math.min(tyRows.length,lyRows.length,10);
    const tyTail=tyRows.slice(-n);
    const lyTail=lyRows.slice(-n);
    let count=0;
    for(let i=0;i<n;i++){
      const tv=parseFloat(tyTail[i].gp)||0;
      const lv=parseFloat(lyTail[i].gp)||0;
      if(direction==='down'?tv<lv:tv>lv) count++;
    }
    consistentDays=count;totalDays=n;
    persistenceLabel=count>=7?'recurring':count>=5?'emerging':'new';
  }

  /* Match TY and LY by index (both should be 14 days, aligned by day-of-week) */
  const maxGP=Math.max(...tyRows.map(r=>Math.abs(parseFloat(r.gp)||0)),...lyRows.map(r=>Math.abs(parseFloat(r.gp)||0)),1);

  /* Detect recovery: last 2 days both improving vs LY */
  const isRecovery=meta&&meta.recovery;
  let recoveryDetected=isRecovery;
  if(recoveryDetected==null&&tyRows.length>=2&&lyRows.length>=2){
    const ty1=parseFloat(tyRows[tyRows.length-2].gp)||0;
    const ty2=parseFloat(tyRows[tyRows.length-1].gp)||0;
    const ly1=parseFloat(lyRows[lyRows.length-2].gp)||0;
    const ly2=parseFloat(lyRows[lyRows.length-1].gp)||0;
    if(direction==='down') recoveryDetected=(ty1>ly1&&ty2>ly2);
    else recoveryDetected=(ty1<ly1&&ty2<ly2);
  }

  /* Persistence summary */
  const persColor=persistenceLabel==='recurring'?'#FF8A91':persistenceLabel==='emerging'?'#FFB55F':'#5FFFF0';
  const recoveryHTML=recoveryDetected?
    `<div style="font-size:10px;font-weight:700;color:#00D4C8;padding:2px 8px;background:rgba(0,212,200,0.12);border:1px solid rgba(0,212,200,0.25);border-radius:10px;animation:recovery-pulse 2s ease-in-out infinite">⬆ Recovery — last 2 days improving</div>`:'';
  const persHTML=`<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:8px 12px;background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid var(--border);flex-wrap:wrap">`+
    `<div style="font-size:11px;color:var(--muted)">Persistence threshold</div>`+
    `<div style="display:flex;gap:2px;align-items:center">`+
    Array.from({length:totalDays},(_, i)=>{
      /* last N days: color each dot by whether it was consistent */
      const idx=tyRows.length-totalDays+i;
      const tv=idx>=0?parseFloat(tyRows[idx].gp)||0:0;
      const lv=idx>=0&&lyRows[idx]?parseFloat(lyRows[idx].gp)||0:0;
      const hit=direction==='down'?tv<lv:tv>lv;
      const dotColor=hit?persColor:'rgba(255,255,255,0.12)';
      return `<div style="width:8px;height:16px;border-radius:2px;background:${dotColor};transition:background 0.3s"></div>`;
    }).join('')+
    `</div>`+
    `<div style="font-size:11px;font-weight:700;color:${persColor}">${consistentDays}/${totalDays} days ${direction}</div>`+
    `<div style="font-size:10px;color:var(--muted);margin-left:auto">`+
    (persistenceLabel==='recurring'?'≥7 = Recurring':persistenceLabel==='emerging'?'5–6 = Emerging':'<5 = New')+
    `</div>`+recoveryHTML+`</div>`;

  let barsHTML='';
  tyRows.forEach((row,i)=>{
    const dt=new Date(row.dt+'T00:00:00');
    const dayLabel=(dt.getMonth()+1)+'/'+dt.getDate();
    const tyGP=parseFloat(row.gp)||0;
    const lyGP=(lyRows[i]&&parseFloat(lyRows[i].gp))||0;
    const yoyPct=lyGP?((tyGP-lyGP)/Math.abs(lyGP))*100:0;
    const isPos=tyGP>=lyGP;
    const barW=Math.max((Math.abs(tyGP)/maxGP)*100,2);
    const pctClass=isPos?'positive':'negative';

    barsHTML+=
      `<div class="yoy-bar-row">`+
      `<div class="yoy-bar-date">${dayLabel}</div>`+
      `<div class="yoy-bar-track"><div class="yoy-bar ${pctClass}" style="width:0%"></div></div>`+
      `<div class="yoy-bar-val">£${Math.round(tyGP).toLocaleString()}</div>`+
      `<div class="yoy-bar-pct ${pctClass}">${isPos?'+':''}${yoyPct.toFixed(0)}%</div>`+
      `</div>`;
  });

  /* Confidence explanation paragraph */
  const confLevel=(meta&&meta.confidence)||null;
  const confExplanation=(meta&&meta.confidence_explanation)||null;
  const bankNote=(meta&&meta.bank_holiday_note)||null;
  let confHTML='';
  if(confExplanation){
    const confColor=confLevel==='Very High'?'#4CAF50':confLevel==='High'?'#66BB6A':confLevel==='Medium'?'#FFB74D':confLevel==='Low'?'#BDBDBD':'#9E9E9E';
    confHTML=`<div style="margin-bottom:10px;padding:10px 14px;background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid var(--border)">`+
      `<div style="font-size:10px;color:var(--muted);margin-bottom:4px">Statistical Confidence</div>`+
      `<div style="font-size:12px;color:${confColor};font-weight:600;margin-bottom:6px">${confLevel} Confidence</div>`+
      `<div style="font-size:11px;color:var(--muted);line-height:1.6">${confExplanation}</div>`+
      (bankNote?`<div style="font-size:10px;color:#FFB74D;margin-top:6px">⚠ ${bankNote}</div>`:'')+
      `</div>`;
  }

  /* Trendline canvas */
  const wrap=document.createElement('div');
  wrap.className='yoy-trend-wrap';
  wrap.innerHTML=
    `<div class="yoy-trend-header"><span>${title} — 14 day daily GP</span><span>YoY growth coloured</span></div>`+
    confHTML+
    barsHTML+
    `<div class="yoy-trendline-wrap"><canvas></canvas></div>`;
  container.innerHTML='';
  container.appendChild(wrap);

  /* Animate bars in */
  requestAnimationFrame(()=>{
    const bars=wrap.querySelectorAll('.yoy-bar');
    tyRows.forEach((row,i)=>{
      const tyGP=parseFloat(row.gp)||0;
      const barW=Math.max((Math.abs(tyGP)/maxGP)*100,2);
      if(bars[i]) bars[i].style.width=barW+'%';
    });
  });

  /* Draw trend line on canvas */
  const canvas=wrap.querySelector('canvas');
  if(canvas){
    const ctx=canvas.getContext('2d');
    const dpr=window.devicePixelRatio||1;
    const rect=canvas.parentElement;
    const w=rect.clientWidth;const h=40;
    canvas.width=w*dpr;canvas.height=h*dpr;
    canvas.style.width=w+'px';canvas.style.height=h+'px';
    ctx.scale(dpr,dpr);

    const vals=tyRows.map(r=>parseFloat(r.gp)||0);
    const lyVals=lyRows.map(r=>parseFloat(r.gp)||0);
    const allVals=[...vals,...lyVals];
    const mn=Math.min(...allVals);const mx=Math.max(...allVals);
    const range=mx-mn||1;

    function drawTrendLine(data,color,width,dashed){
      if(!data.length) return;
      ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;
      ctx.setLineDash(dashed?[4,3]:[]);
      const step=w/(data.length-1||1);
      data.forEach((v,i)=>{
        const x=i*step;
        const y=2+(1-(v-mn)/range)*(h-4);
        if(i===0) ctx.moveTo(x,y);else ctx.lineTo(x,y);
      });
      ctx.stroke();
    }

    drawTrendLine(lyVals,'rgba(255,255,255,0.15)',1.5,true);
    drawTrendLine(vals,'rgba(146,95,255,0.85)',2,false);

    /* Dot on last TY value */
    if(vals.length){
      const lastX=(vals.length-1)*(w/(vals.length-1||1));
      const lastY=2+(1-(vals[vals.length-1]-mn)/range)*(h-4);
      ctx.beginPath();
      ctx.arc(lastX,lastY,3,0,Math.PI*2);
      ctx.fillStyle='rgba(146,95,255,1)';ctx.fill();
    }
  }
}

/* Per-driver conversation history — keyed by panel id */
const driverHistory={};

function openDriverAsk(id){
  const panel=document.getElementById(id);
  if(!panel) return;
  const isOpen=panel.style.display!=='none';
  panel.style.display=isOpen?'none':'block';
  if(!isOpen){
    panel.querySelector('.ask-input').focus();
  }
}

function getDriverContext(panel){
  const wrap=panel.closest('.dig-wrap');
  let ctx='';
  if(wrap){
    /* Collect all narrative paragraphs and heading above this dig-wrap */
    const parts=[];
    let prev=wrap.previousElementSibling;
    while(prev){
      if(prev.tagName==='H3'||prev.tagName==='P'){
        parts.unshift(prev.textContent);
      }
      if(prev.tagName==='H3') break;
      prev=prev.previousElementSibling;
    }
    ctx=parts.join('\n');
    /* Also grab the SQL query if present — tells the AI exactly which table/filters apply */
    const sqlCode=wrap.querySelector('pre.dig-sql code');
    if(sqlCode) ctx+='\n\nOriginal SQL used for this driver:\n'+sqlCode.textContent;
  }
  return ctx;
}

function buildSqlButton(sqlQueries){
  if(!sqlQueries||!sqlQueries.length) return '';
  const uid='sql-'+Math.random().toString(36).slice(2,8);
  const successCount=sqlQueries.filter(q=>q.success).length;
  const failCount=sqlQueries.length-successCount;
  const totalRows=sqlQueries.filter(q=>q.success).reduce((s,q)=>s+q.rows,0);
  let summaryParts=[];
  if(successCount) summaryParts.push(successCount+' successful');
  if(failCount) summaryParts.push(failCount+' failed');

  let html='<button class="view-sql-btn" data-sql-uid="'+uid+'">'
    +'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px">'
    +'<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>'
    +'<rect x="9" y="3" width="6" height="4" rx="1"/></svg>'
    +'Investigation trail</button>';
  html+='<div id="'+uid+'" class="chat-sql-detail">';

  /* Trail header */
  html+='<div style="padding:12px 16px;margin-bottom:12px;background:rgba(84,46,145,0.08);border-left:3px solid var(--accent-light);border-radius:0 10px 10px 0">'
    +'<div style="font-size:10px;font-weight:700;color:var(--accent-light);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">How we got this answer</div>'
    +'<div style="font-size:12px;color:#e2d6f0">Ran <strong>'+sqlQueries.length+' quer'+(sqlQueries.length===1?'y':'ies')+'</strong> against BigQuery'
    +(totalRows?' returning <strong>'+totalRows.toLocaleString()+' row'+(totalRows===1?'':'s')+'</strong> of data':'')
    +'</div></div>';

  /* Each query as a trail step */
  sqlQueries.forEach((q,i)=>{
    const escaped=q.sql.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const isSuccess=q.success;
    const dotColor=isSuccess?'var(--accent-light)':'var(--red)';
    const borderColor=isSuccess?'var(--accent-light)':'var(--red)';
    const isLast=i===sqlQueries.length-1;

    html+='<div style="position:relative;padding-left:36px;margin-bottom:'+(isLast?'0':'16')+'px">';
    /* Connector line */
    if(!isLast) html+='<div style="position:absolute;left:11px;top:22px;bottom:-16px;width:2px;background:linear-gradient(to bottom,'+borderColor+',rgba(84,46,145,0.08))"></div>';
    /* Dot */
    html+='<div style="position:absolute;left:0;top:2px;width:24px;height:20px;border-radius:10px;border:2px solid '+dotColor+';background:var(--bg);display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:800;color:'+dotColor+'">'+(i+1)+'</div>';
    /* Content */
    html+='<div style="padding:10px 14px;background:rgba(15,23,42,0.5);border:1px solid var(--border);border-radius:8px">';
    if(isSuccess){
      html+='<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
        +'<span style="font-size:10px;font-weight:700;color:var(--accent-light);text-transform:uppercase;letter-spacing:.5px">Query '+(i+1)+'</span>'
        +'<span style="font-size:10px;color:#34d399;font-weight:600">'+q.rows+' row'+(q.rows===1?'':'s')+' returned</span>'
        +'<button class="sql-copy-btn" style="margin-left:auto">Copy SQL</button>'
        +'</div>';
      /* Show sample data preview if available */
      if(q.sample_data){
        const sampleLines=q.sample_data.split('\n').slice(0,3);
        html+='<div style="font-size:10px;color:var(--muted);margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Sample results</div>';
        html+='<div style="font-size:11px;color:#cbd5e1;margin-bottom:8px;padding:8px;background:rgba(0,0,0,0.2);border-radius:6px;overflow-x:auto;max-height:80px">';
        sampleLines.forEach(line=>{
          try{
            const obj=JSON.parse(line);
            const pairs=Object.entries(obj).map(([k,v])=>'<span style="color:var(--muted)">'+k+':</span> <span style="color:#f1f5f9">'+v+'</span>');
            html+='<div style="white-space:nowrap;margin-bottom:2px">'+pairs.join(' &middot; ')+'</div>';
          }catch{
            html+='<div style="white-space:nowrap;margin-bottom:2px">'+line.replace(/</g,'&lt;').replace(/>/g,'&gt;')+'</div>';
          }
        });
        if(q.rows>3) html+='<div style="color:var(--muted);font-style:italic;margin-top:4px">…and '+(q.rows-3)+' more row'+(q.rows-3===1?'':'s')+'</div>';
        html+='</div>';
      }
    }else{
      const errEsc=(q.error||'Unknown error').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      html+='<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
        +'<span style="font-size:10px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.5px">Query '+(i+1)+' — Failed</span>'
        +'<button class="sql-copy-btn" style="margin-left:auto">Copy SQL</button>'
        +'</div>';
      html+='<div style="font-size:11px;color:var(--red);margin-bottom:8px;padding:8px;background:rgba(248,113,113,0.06);border-radius:6px;border-left:2px solid var(--red)">'+errEsc+'</div>';
    }
    /* SQL query (collapsed by default) */
    const sqlUid='sqld-'+Math.random().toString(36).slice(2,8);
    html+='<button class="view-sql-btn" data-sql-uid="'+sqlUid+'" style="font-size:10px;padding:3px 8px;margin:0">Show SQL</button>';
    html+='<div id="'+sqlUid+'" class="chat-sql-detail"><pre>'+escaped+'</pre></div>';
    html+='</div></div>';
  });

  html+='</div>';
  return html;
}

function renderAIChart(container,chartData){
  if(!chartData||!chartData.points||chartData.points.length<2) return;
  const wrap=document.createElement('div');
  wrap.className='ai-chart-wrap';

  const isTime=chartData.type==='timeseries';
  const pts=chartData.points;
  const lyPts=chartData.ly_points||[];
  const deltas=chartData.delta_values||[];
  const allVals=pts.map(p=>p.value).concat(lyPts.map(p=>p.value));
  const maxV=Math.max(...allVals);
  const minV=Math.min(...allVals);
  const range=maxV-minV||1;
  const dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

  let title=chartData.label||'Value';
  if(isTime) title+=' — '+pts.length+' day trend';
  let barsHTML='';
  pts.forEach((p,i)=>{
    const h=((p.value-minV)/range)*110+10;
    const lyVal=lyPts[i]?lyPts[i].value:null;
    const deltaVal=deltas[i]!==undefined?deltas[i]:null;
    const prevVal=i>0?pts[i-1].value:null;
    /* Determine up/down: prefer LY comparison, then delta column, then previous day */
    const isUp=lyVal!==null?p.value>=lyVal:(deltaVal!==null?deltaVal>=0:(prevVal!==null?p.value>=prevVal:true));
    const gradTop=isUp?'#00D4C8':'#FF8A91';
    const gradBot=isUp?'#00B0A6':'#FF5F68';
    let label='';
    if(isTime&&p.date){
      const dt=new Date(p.date+'T00:00:00');
      label=dayNames[dt.getDay()]+' '+(dt.getMonth()+1)+'/'+dt.getDate();
    }else{
      label=p.category||'';
    }
    const fmtVal=p.value>=1000?'\u00A3'+Math.round(p.value).toLocaleString():p.value.toFixed(1);
    /* Growth tooltip: show vs LY with % change, or delta, or vs previous */
    let growthHTML='';
    if(lyVal!==null){
      const diff=p.value-lyVal;
      const pct=lyVal!==0?((diff/lyVal)*100).toFixed(1):'n/a';
      growthHTML='<div style="color:'+(isUp?'#34d399':'#f87171')+'">vs LY: \u00A3'+Math.round(lyVal).toLocaleString()+' ('+(isUp?'+':'')+pct+'%)</div>';
    }else if(deltaVal!==null){
      growthHTML='<div style="color:'+(isUp?'#34d399':'#f87171')+'">'+(isUp?'+':'')+deltaVal.toFixed(1)+'% vs LY</div>';
    }else if(prevVal!==null){
      const diff=p.value-prevVal;
      const pct=prevVal!==0?((diff/prevVal)*100).toFixed(1):'n/a';
      growthHTML='<div style="color:'+(isUp?'#34d399':'#f87171')+'">vs prev: '+(isUp?'+':'')+pct+'%</div>';
    }
    barsHTML+=
      '<div class="bar-col">'+
      '<div class="tooltip"><div style="font-weight:700;margin-bottom:2px">'+label+'</div><div>'+fmtVal+'</div>'+growthHTML+'</div>'+
      '<div class="bar" style="height:0px;background:linear-gradient(to top,'+gradBot+','+gradTop+')"></div>'+
      '<div class="bar-label">'+label+'</div></div>';
  });

  wrap.innerHTML='<div class="ai-chart-title">'+title+'</div>'+
    '<div class="ai-chart-container">'+barsHTML+'</div>'+
    '<div class="ai-chart-trendline"><canvas></canvas></div>';
  container.appendChild(wrap);

  /* Animate bars */
  requestAnimationFrame(()=>{
    requestAnimationFrame(()=>{
      const bars=wrap.querySelectorAll('.bar');
      pts.forEach((p,i)=>{
        const h=((p.value-minV)/range)*110+10;
        if(bars[i]) bars[i].style.height=h+'px';
      });
    });
  });

  /* Draw trendline on canvas */
  const canvas=wrap.querySelector('canvas');
  if(canvas&&pts.length>=2){
    const ctx=canvas.getContext('2d');
    const dpr=window.devicePixelRatio||1;
    const cw=canvas.parentElement.clientWidth;const ch=30;
    canvas.width=cw*dpr;canvas.height=ch*dpr;
    canvas.style.width=cw+'px';canvas.style.height=ch+'px';
    ctx.scale(dpr,dpr);

    function drawLine(data,color,width,dashed){
      if(!data.length) return;
      ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;
      ctx.setLineDash(dashed?[4,3]:[]);
      const step=cw/(data.length-1||1);
      data.forEach((v,i)=>{
        const x=i*step;
        const y=2+(1-(v-minV)/range)*(ch-4);
        if(i===0) ctx.moveTo(x,y);else ctx.lineTo(x,y);
      });
      ctx.stroke();
    }

    if(lyPts.length) drawLine(lyPts.map(p=>p.value),'rgba(255,255,255,0.15)',1.5,true);
    drawLine(pts.map(p=>p.value),'rgba(146,95,255,0.85)',2,false);

    /* Dot on last value */
    const vals=pts.map(p=>p.value);
    const lastX=(vals.length-1)*(cw/(vals.length-1||1));
    const lastY=2+(1-(vals[vals.length-1]-minV)/range)*(ch-4);
    ctx.beginPath();ctx.arc(lastX,lastY,3,0,Math.PI*2);
    ctx.fillStyle='rgba(146,95,255,1)';ctx.fill();

    /* Linear regression trend line */
    const n=vals.length;
    const sumX=vals.reduce((_,__,i)=>_+i,0);
    const sumY=vals.reduce((s,v)=>s+v,0);
    const sumXY=vals.reduce((s,v,i)=>s+i*v,0);
    const sumX2=vals.reduce((s,_,i)=>s+i*i,0);
    const slope=(n*sumXY-sumX*sumY)/(n*sumX2-sumX*sumX);
    const intercept=(sumY-slope*sumX)/n;
    const trendVals=vals.map((_,i)=>intercept+slope*i);
    drawLine(trendVals,'rgba(255,180,50,0.5)',1.5,true);
  }
}

/* Delegate click handlers for SQL view/copy buttons */
document.addEventListener('click',function(e){
  const sqlBtn=e.target.closest('.view-sql-btn');
  if(sqlBtn){
    const uid=sqlBtn.getAttribute('data-sql-uid');
    const d=document.getElementById(uid);
    if(d){
      d.classList.toggle('open');
      sqlBtn.textContent=d.classList.contains('open')?'Hide SQL':'View SQL';
    }
    return;
  }
  const copyBtn=e.target.closest('.sql-copy-btn');
  if(copyBtn){
    const pre=copyBtn.closest('.sql-block').querySelector('pre');
    navigator.clipboard.writeText(pre.textContent).then(()=>{
      copyBtn.textContent='Copied!';
      setTimeout(()=>copyBtn.textContent='Copy',1500);
    });
  }
});

function addDriverMessage(responseDiv,role,content){
  const msg=document.createElement('div');
  msg.className='chat-msg '+role;
  if(role==='assistant') msg.innerHTML=content;
  else msg.textContent=content;
  responseDiv.appendChild(msg);
}

function addDriverReplyInput(responseDiv,id){
  /* Remove any existing reply inputs */
  responseDiv.querySelectorAll('.chat-reply-wrap').forEach(el=>el.remove());
  const wrap=document.createElement('div');
  wrap.className='chat-reply-wrap';
  wrap.innerHTML='<input type="text" class="chat-input chat-reply-input" placeholder="Ask a follow-up…">'
    +'<button class="chat-send chat-reply-send" onclick="submitDriverReply(this,\''+id+'\')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg></button>';
  responseDiv.appendChild(wrap);
  const inp=wrap.querySelector('.chat-reply-input');
  inp.addEventListener('keydown',function(e){if(e.key==='Enter')submitDriverReply(wrap.querySelector('.chat-reply-send'),id)});
  inp.focus();
}

function submitDriverAsk(id){
  const panel=document.getElementById(id);
  const input=panel.querySelector('.ask-input');
  const responseDiv=document.getElementById(id+'-response');
  const question=input.value.trim();
  if(!question) return;

  /* Init history for this driver */
  if(!driverHistory[id]) driverHistory[id]=[];
  const driverContext=getDriverContext(panel);

  /* Show user message */
  addDriverMessage(responseDiv,'user',question);
  input.value='';
  input.style.display='none';
  input.closest('.ask-input-wrap').querySelector('.ask-submit').style.display='none';

  /* Loading stepper */
  const loader=createAILoadingEl();
  const loadingWrap=document.createElement('div');
  loadingWrap.className='chat-msg assistant loading';
  loadingWrap.appendChild(loader);
  responseDiv.appendChild(loadingWrap);
  startAILoadingStepper(loader);

  driverHistory[id].push({role:'user',content:question});

  fetch((window.__apiBase||'')+'/api/ask',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      question:question,
      driver_context:driverContext,
      conversation_history:driverHistory[id].slice(-10),
      mode:'driver',
      field_discovery:window.__fieldDiscovery||null
    })
  })
  .then(r=>r.json())
  .then(data=>{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    } else if(data.sql_queries&&data.sql_queries.length>0){
      content+='<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }
    addDriverMessage(responseDiv,'assistant',content);
    if(data.chart_data) renderAIChart(responseDiv,data.chart_data);
    driverHistory[id].push({role:'assistant',content:data.answer||''});
    addDriverReplyInput(responseDiv,id);
  })
  .catch(err=>{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    addDriverMessage(responseDiv,'assistant','<span class="ask-error">Failed to connect: '+err.message+'</span>');
    addDriverReplyInput(responseDiv,id);
  });
}

function submitDriverReply(btn,id){
  const wrap=btn.closest('.chat-reply-wrap');
  const input=wrap.querySelector('.chat-reply-input');
  const question=input.value.trim();
  if(!question) return;

  const responseDiv=document.getElementById(id+'-response');
  const panel=document.getElementById(id);
  const driverContext=getDriverContext(panel);

  /* Convert reply input to user message */
  const userMsg=document.createElement('div');
  userMsg.className='chat-msg user';
  userMsg.textContent=question;
  wrap.replaceWith(userMsg);

  /* Loading */
  const loader=createAILoadingEl();
  const loadingWrap=document.createElement('div');
  loadingWrap.className='chat-msg assistant loading';
  loadingWrap.appendChild(loader);
  responseDiv.appendChild(loadingWrap);
  startAILoadingStepper(loader);

  if(!driverHistory[id]) driverHistory[id]=[];
  driverHistory[id].push({role:'user',content:question});

  fetch((window.__apiBase||'')+'/api/ask',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      question:question,
      driver_context:driverContext,
      conversation_history:driverHistory[id].slice(-10),
      mode:'driver',
      field_discovery:window.__fieldDiscovery||null
    })
  })
  .then(r=>r.json())
  .then(data=>{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    } else if(data.sql_queries&&data.sql_queries.length>0){
      content+='<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }
    addDriverMessage(responseDiv,'assistant',content);
    if(data.chart_data) renderAIChart(responseDiv,data.chart_data);
    driverHistory[id].push({role:'assistant',content:data.answer||''});
    addDriverReplyInput(responseDiv,id);
  })
  .catch(err=>{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    addDriverMessage(responseDiv,'assistant','<span class="ask-error">Connection error: '+err.message+'</span>');
    addDriverReplyInput(responseDiv,id);
  });
}

/* ── General chat panel ── */
let chatHistory=[];
function toggleChat(){
  const panel=document.getElementById('chatPanel');
  const isOpen=panel.style.display!=='none';
  panel.style.display=isOpen?'none':'flex';
  if(!isOpen){
    /* Show input bar on first open */
    const inputWrap=document.querySelector('.chat-input-wrap');
    inputWrap.style.display='flex';
    document.getElementById('chatInput').focus();
  }
}

/* ── Resize handle for chat sidebar ── */
(function(){
  const handle=document.getElementById('chatResizeHandle');
  const panel=document.getElementById('chatPanel');
  if(!handle||!panel) return;
  let dragging=false,startX=0,startW=0;
  handle.addEventListener('mousedown',function(e){
    e.preventDefault();
    dragging=true;startX=e.clientX;startW=panel.offsetWidth;
    handle.classList.add('active');
    document.body.style.cursor='col-resize';
    document.body.style.userSelect='none';
  });
  document.addEventListener('mousemove',function(e){
    if(!dragging) return;
    const diff=startX-e.clientX;
    const newW=Math.min(Math.max(startW+diff,320),window.innerWidth*0.85);
    panel.style.width=newW+'px';
    panel.style.transition='none';
  });
  document.addEventListener('mouseup',function(){
    if(!dragging) return;
    dragging=false;
    handle.classList.remove('active');
    document.body.style.cursor='';
    document.body.style.userSelect='';
    panel.style.transition='';
  });
  /* Touch support for tablets */
  handle.addEventListener('touchstart',function(e){
    const t=e.touches[0];
    dragging=true;startX=t.clientX;startW=panel.offsetWidth;
    handle.classList.add('active');
  },{passive:true});
  document.addEventListener('touchmove',function(e){
    if(!dragging) return;
    const t=e.touches[0];
    const diff=startX-t.clientX;
    const newW=Math.min(Math.max(startW+diff,320),window.innerWidth*0.85);
    panel.style.width=newW+'px';
    panel.style.transition='none';
  });
  document.addEventListener('touchend',function(){
    if(!dragging) return;
    dragging=false;
    handle.classList.remove('active');
    panel.style.transition='';
  });
})();

function submitChat(){
  const inputWrap=document.querySelector('.chat-input-wrap');
  const input=document.getElementById('chatInput');
  const messagesDiv=document.getElementById('chatMessages');
  const question=input.value.trim();
  if(!question) return;

  /* Add user message bubble */
  const userMsg=document.createElement('div');
  userMsg.className='chat-msg user';
  userMsg.textContent=question;
  messagesDiv.appendChild(userMsg);

  /* Hide the input bar — it becomes just a sent message */
  inputWrap.style.display='none';
  input.value='';

  /* Add animated loading stepper */
  const loadingMsg=document.createElement('div');
  loadingMsg.className='chat-msg assistant loading';
  const chatLoader=createAILoadingEl();
  loadingMsg.appendChild(chatLoader);
  startAILoadingStepper(chatLoader);
  messagesDiv.appendChild(loadingMsg);
  messagesDiv.scrollTop=messagesDiv.scrollHeight;

  chatHistory.push({role:'user',content:question});

  fetch((window.__apiBase||'')+'/api/ask',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      question:question,
      conversation_history:chatHistory.slice(-10),
      mode:'general',
      field_discovery:window.__fieldDiscovery||null
    })
  })
  .then(r=>r.json())
  .then(data=>{
    stopAILoadingStepper(chatLoader);
    messagesDiv.removeChild(loadingMsg);

    const assistantMsg=document.createElement('div');
    assistantMsg.className='chat-msg assistant';
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    } else if(data.sql_queries&&data.sql_queries.length>0){
      content+='\n<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }
    assistantMsg.innerHTML=content;
    messagesDiv.appendChild(assistantMsg);
    if(data.chart_data) renderAIChart(messagesDiv,data.chart_data);

    chatHistory.push({role:'assistant',content:data.answer||''});

    /* Add a new reply input inline at the bottom of the transcript */
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  })
  .catch(err=>{
    messagesDiv.removeChild(loadingMsg);
    const errMsg=document.createElement('div');
    errMsg.className='chat-msg assistant';
    errMsg.innerHTML='<span class="ask-error">Connection error: '+err.message+'</span>';
    messagesDiv.appendChild(errMsg);
    /* Still offer a reply input */
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  });
}

function addChatReplyInput(container){
  /* Remove any existing inline reply inputs */
  container.querySelectorAll('.chat-reply-wrap').forEach(el=>el.remove());

  const wrap=document.createElement('div');
  wrap.className='chat-reply-wrap';
  wrap.innerHTML='<input type="text" class="chat-input chat-reply-input" placeholder="Ask a follow-up...">'
    +'<button class="chat-send chat-reply-send" onclick="submitChatReply(this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg></button>';
  container.appendChild(wrap);
  const replyInput=wrap.querySelector('.chat-reply-input');
  replyInput.addEventListener('keydown',function(e){if(e.key==='Enter')submitChatReply(wrap.querySelector('.chat-reply-send'))});
  replyInput.focus();
}

function submitChatReply(btn){
  const wrap=btn.closest('.chat-reply-wrap');
  const input=wrap.querySelector('.chat-reply-input');
  const question=input.value.trim();
  if(!question) return;

  const messagesDiv=document.getElementById('chatMessages');

  /* Convert this reply input into a user message */
  const userMsg=document.createElement('div');
  userMsg.className='chat-msg user';
  userMsg.textContent=question;
  wrap.replaceWith(userMsg);

  /* Animated loading stepper */
  const loadingMsg=document.createElement('div');
  loadingMsg.className='chat-msg assistant loading';
  const replyLoader=createAILoadingEl();
  loadingMsg.appendChild(replyLoader);
  startAILoadingStepper(replyLoader);
  messagesDiv.appendChild(loadingMsg);
  messagesDiv.scrollTop=messagesDiv.scrollHeight;

  chatHistory.push({role:'user',content:question});

  fetch((window.__apiBase||'')+'/api/ask',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      question:question,
      conversation_history:chatHistory.slice(-10),
      mode:'general',
      field_discovery:window.__fieldDiscovery||null
    })
  })
  .then(r=>r.json())
  .then(data=>{
    stopAILoadingStepper(replyLoader);
    messagesDiv.removeChild(loadingMsg);
    const assistantMsg=document.createElement('div');
    assistantMsg.className='chat-msg assistant';
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    } else if(data.sql_queries&&data.sql_queries.length>0){
      content+='\n<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }
    assistantMsg.innerHTML=content;
    messagesDiv.appendChild(assistantMsg);
    if(data.chart_data) renderAIChart(messagesDiv,data.chart_data);
    chatHistory.push({role:'assistant',content:data.answer||''});
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  })
  .catch(err=>{
    messagesDiv.removeChild(loadingMsg);
    const errMsg=document.createElement('div');
    errMsg.className='chat-msg assistant';
    errMsg.innerHTML='<span class="ask-error">Connection error: '+err.message+'</span>';
    messagesDiv.appendChild(errMsg);
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  });
}

/* ── Investigation trail toggle ── */
function toggleTrail(){
  const body=document.getElementById('trailBody');
  const btn=document.getElementById('trailToggle');
  if(!body||!btn) return;
  const willOpen=!body.classList.contains('open');
  if(willOpen){
    body.style.maxHeight=body.scrollHeight+'px';
    body.classList.add('open');
    btn.classList.add('open');
    /* After transition, remove max-height cap so content is never clipped */
    setTimeout(function(){body.style.maxHeight='none';},700);
  }else{
    /* Set explicit height first so transition works for closing */
    body.style.maxHeight=body.scrollHeight+'px';
    body.offsetHeight; /* force reflow */
    body.style.maxHeight='0';
    body.classList.remove('open');
    btn.classList.remove('open');
  }
  const isOpen=willOpen;
  /* Update button text — find text node after svg */
  const nodes=btn.childNodes;
  for(let i=0;i<nodes.length;i++){
    if(nodes[i].nodeType===3&&nodes[i].textContent.trim()){
      nodes[i].textContent=isOpen?' Hide full investigation trail':' Show full investigation trail';
      break;
    }
  }
}

/* ── Open investigations from toolbar badge ── */
function openInvestigations(){
  const section=document.querySelector('.trail-section');
  const body=document.getElementById('trailBody');
  if(!section) return;
  /* Open the trail if it's closed */
  if(body&&!body.classList.contains('open')){
    toggleTrail();
  }
  /* Scroll so the section header is right below the sticky toolbar */
  setTimeout(function(){
    const hdr=document.querySelector('.hdr');
    const offset=hdr?hdr.offsetHeight+8:50;
    const top=section.getBoundingClientRect().top+window.scrollY-offset;
    window.scrollTo({top:top,behavior:'smooth'});
  },100);
}

/* ── Scroll-reactive animations — BIDIRECTIONAL ── */
(function(){
  /* Enable animation classes — content visible by default without JS */
  document.querySelectorAll('[data-animate]').forEach(el=>el.classList.add('animate-ready'));

  let chartBuilt=false;

  /* 1. MAIN OBSERVER — ONE-WAY reveal only, never hides content once visible */
  const mainRevealed=new WeakSet();
  const mainObs=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting&&!mainRevealed.has(e.target)){
        mainRevealed.add(e.target);
        e.target.classList.add('in-view');
        e.target.classList.remove('out-view-top','out-view-bottom','animate-ready');
        /* Build chart on first reveal */
        if(!chartBuilt&&e.target.querySelector('#trendChart')){
          chartBuilt=true;buildChart();
        }
      }
    });
  },{threshold:0.15,rootMargin:'0px 0px 60px 0px'});
  document.querySelectorAll('[data-animate]').forEach(el=>mainObs.observe(el));

  /* 3. Metric pulse on scroll — positive grows, negative sinks */
  const metricObs=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){e.target.classList.add('metric-active');}
      else{e.target.classList.remove('metric-active');}
    });
  },{threshold:0.5});
  document.querySelectorAll('[data-metric]').forEach(el=>metricObs.observe(el));

  /* 4. CountUp animation */
  const counted=new WeakSet();
  const countObs=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting&&!counted.has(e.target)){
        counted.add(e.target);
        const el=e.target;
        const raw=el.dataset.target||'0';
        const target=parseFloat(raw.replace(/,/g,''));
        const prefix=el.dataset.prefix||'';
        const decimals=parseInt(el.dataset.decimals||'0');
        const dur=800;const start=performance.now();
        function tick(now){
          const p=Math.min((now-start)/dur,1);
          const eased=1-Math.pow(1-p,3);
          el.innerHTML=prefix+(target*eased).toLocaleString(undefined,{minimumFractionDigits:decimals,maximumFractionDigits:decimals});
          if(p<1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      }
    });
  },{threshold:0.2});
  document.querySelectorAll('[data-countup]').forEach(el=>countObs.observe(el));

  /* 5. Staggered reveal for narrative sub-elements — ONE-WAY fade in only, never hides */
  const narRevealed=new WeakSet();
  const narObs=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting&&!narRevealed.has(e.target)){
        narRevealed.add(e.target);
        e.target.style.opacity='1';
        e.target.style.transform='translateY(0)';
      }
    });
  },{threshold:0.01,rootMargin:'0px 0px 60px 0px'});
  document.querySelectorAll('.nar h2,.nar blockquote,.nar table,.dig-wrap,.nar>p,.nar>ul,.nar>ol').forEach((el,i)=>{
    el.style.opacity='0';
    el.style.transform='translateY(16px)';
    el.style.transition=`opacity 0.45s cubic-bezier(.16,1,.3,1) ${(i%6)*40}ms, transform 0.45s cubic-bezier(.16,1,.3,1) ${(i%6)*40}ms`;
    narObs.observe(el);
  });

  /* 6. Immediately reveal anything already in viewport on load */
  requestAnimationFrame(()=>{
    document.querySelectorAll('[data-animate]').forEach(el=>{
      const rect=el.getBoundingClientRect();
      if(rect.top<window.innerHeight&&rect.bottom>0){
        el.classList.add('in-view');
      }
    });
    if(!chartBuilt){
      const cc=document.getElementById('trendChart');
      if(cc&&cc.getBoundingClientRect().top<window.innerHeight){chartBuilt=true;buildChart();}
    }
  });

  /* 7. Mouse-tracking hover ripple on cards */
  document.querySelectorAll('.card,.pcard').forEach(el=>{
    el.addEventListener('mousemove',(e)=>{
      const rect=el.getBoundingClientRect();
      el.style.setProperty('--mx',((e.clientX-rect.left)/rect.width*100)+'%');
      el.style.setProperty('--my',((e.clientY-rect.top)/rect.height*100)+'%');
    });
  });

  /* Hover sparkle on metric values */
  document.querySelectorAll('.card .val,.pcard .pv').forEach(el=>{
    el.addEventListener('mouseenter',()=>{
      el.style.transition='letter-spacing 0.3s ease-out';
      el.style.letterSpacing='-0.5px';
      setTimeout(()=>{el.style.letterSpacing='-1.5px'},150);
    });
  });

  /* 9. Progress indicator — thin bar at top showing scroll progress */
  const bar=document.createElement('div');
  bar.style.cssText='position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--yellow));z-index:999;transition:width 0.1s linear;width:0';
  document.body.appendChild(bar);
  window.addEventListener('scroll',()=>{
    const pct=(window.scrollY/(document.body.scrollHeight-window.innerHeight))*100;
    bar.style.width=pct+'%';
  },{passive:true});

  /* 10. Init driver trend badges + buttons from computed data */
  (function initDriverTrends(){
    const trends=window.__driverTrends||{};
    if(!Object.keys(trends).length) return;
    const headings=document.querySelectorAll('h3[data-driver-idx]');

    headings.forEach(h3=>{
      const trendKey=h3.getAttribute('data-trend-key');
      /* Find the pills line — next sibling div.driver-pills */
      const pillsDiv=h3.nextElementSibling&&h3.nextElementSibling.classList.contains('driver-pills')?h3.nextElementSibling:null;
      const btn=pillsDiv?pillsDiv.querySelector('.view-trend-btn'):h3.querySelector('.view-trend-btn');
      const tid=btn?btn.getAttribute('data-trend-id'):null;

      /* No trend data for this heading — leave as-is */
      if(!trendKey||!trends[trendKey]) return;

      const td=trends[trendKey];
      const p=td.persistence||'new';
      const cd=td.consistent_days||0;
      const tot=td.total_days||10;
      const recovery=td.recovery||false;

      if(tid){
        const container=document.getElementById(tid);
        if(container) container._matchedData=td;
      }

      /* Move persistence badge (recurring/emerging/new) from h3 to pills line */
      const target=pillsDiv||h3;
      const oldBadge=h3.querySelector('.badge-recurring,.badge-emerging,.badge-new');
      if(oldBadge&&target!==h3){
        oldBadge.remove();
        target.prepend(oldBadge);
      }

      /* Remove any old confidence badge from h3 (shouldn't be there, but defensive) */
      const oldConfBadge=h3.querySelector('[class^="badge-confidence-"]');
      if(oldConfBadge) oldConfBadge.remove();

      /* Insert confidence badge into pills line */
      const conf=(td.confidence||'Low');
      const confSlug=conf.toLowerCase().replace(/\s+/g,'-');
      const badge=document.createElement('span');
      badge.className='badge-confidence-'+confSlug;
      badge.textContent=conf+' confidence';
      const tip=document.createElement('span');
      tip.className='conf-tip';
      tip.textContent=cd+'/'+tot+' days consistent. Click Trend for full analysis.';
      badge.appendChild(tip);
      /* Insert confidence pill at the start of the pills line (before trend btn, after persistence badge) */
      if(btn) target.insertBefore(badge,btn);
      else target.appendChild(badge);

      if(btn){
        btn.style.display='';
        btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>Trend';
      }

      if(recovery){
        const recBadge=document.createElement('span');
        recBadge.className='badge-recovery';
        recBadge.textContent='Recovery';
        if(btn) target.insertBefore(recBadge,btn);
        else target.appendChild(recBadge);
      }
    });
  })();
})();

/* Chart fallback — if intersection observer didn't trigger (e.g. chart visible on load) */
setTimeout(function(){if(!chartBuilt&&data&&data.length)buildChart();},800);

/* (Sticky section label removed — replaced by banner) */

/* Refresh button — cascading collapse animation */
function triggerRefresh(){
  const sections=document.querySelectorAll('.section-gap, .grid4, .grid3');
  sections.forEach((el,i)=>{
    setTimeout(()=>{
      el.classList.add('collapsing');
    }, i * 80);
  });
  setTimeout(()=>{
    window.location.reload();
  }, Math.max(sections.length * 80 + 500, 600));
}

/* ── Archive viewer ── */
let archiveOpen = false;
function toggleArchive(){
  const overlay = document.getElementById('archiveOverlay');
  archiveOpen = !archiveOpen;
  if(archiveOpen){
    overlay.classList.add('open');
    loadArchive();
  } else {
    overlay.classList.remove('open');
  }
}
function loadArchive(){
  const list = document.getElementById('archiveList');
  list.innerHTML = '<div class="archive-empty">Loading...</div>';
  fetch('archive.json')
    .then(r => r.ok ? r.json() : [])
    .then(entries => {
      if(!entries.length){
        list.innerHTML = '<div class="archive-empty">No archived briefings yet.</div>';
        return;
      }
      list.innerHTML = entries.map(e => {
        const d = new Date(e.date + 'T00:00:00');
        const dayName = d.toLocaleDateString('en-GB', {weekday:'short'});
        const dateStr = d.toLocaleDateString('en-GB', {day:'numeric',month:'short',year:'numeric'});
        return `<div class="archive-item" onclick="window.location.href='${e.file}'">
          <span class="archive-date">${dayName} ${dateStr}</span>
          <span class="archive-headline">${e.headline || '—'}</span>
          <span class="archive-size">${e.size_kb}kb</span>
        </div>`;
      }).join('');
    })
    .catch(() => {
      list.innerHTML = '<div class="archive-empty">Could not load archive. Run the briefing to generate archive.json.</div>';
    });
}
// Close archive on escape or clicking outside
document.addEventListener('keydown', e => {
  if(e.key === 'Escape' && archiveOpen) toggleArchive();
});
