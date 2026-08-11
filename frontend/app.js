const API_BASE = window.BUILDYOURPC_API || '';

const state = {
  step: 1,
  device_type: 'desktop',
  budget: 800,
  currency: 'USD',
  country: 'US',
  language: 'en',
  use_cases: ['Gaming'],
  games: [],
  preferences: [],
  existing_parts: [],
  target_fps: null,
  resolution: null,
  result: null,
  preset: 'smart'
};

const el = (id) => document.getElementById(id);
const q = (sel, root=document) => root.querySelector(sel);
const qa = (sel, root=document) => [...root.querySelectorAll(sel)];
let config = {countries:[], languages:[], games:[], currencies:{}, kofi:'https://ko-fi.com/simbawwyy00'};

function toast(msg){const t=el('toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(()=>t.classList.remove('show'),2500)}
function currencySymbol(code){return config.currencies?.[code] || code}
function fmtMoney(value, code=state.currency){return `${currencySymbol(code)}${Number(value).toLocaleString(undefined,{maximumFractionDigits:0})}`}
function countryName(code){return config.countries.find(x=>x.code===code)?.name || code}
function updateCountryUI(){el('countryLabel').textContent=state.country;el('budgetCurrency').textContent=state.currency;el('currencySymbol').textContent=currencySymbol(state.currency);el('langBtn').textContent=(config.languages.find(x=>x.code===state.language)?.code||'en').toUpperCase();}
function updateBudgetUI(){el('budgetInput').value=Math.round(state.budget);el('budgetSlider').value=Math.min(5000,Math.max(150,state.budget));el('heroBudget').textContent=fmtMoney(state.budget);const extra=Math.round(state.budget*0.07);const title=el('whatIfBudgetTitle');if(title)title.textContent=`I can add ${fmtMoney(extra)}`;}

async function loadExistingBuild(){
  const m=location.pathname.match(/^\/build\/([A-Za-z0-9_-]+)$/);
  if(!m) return false;
  try{
    const r=await fetch(API_BASE + `/api/builds/${m[1]}`);
    const d=await r.json();
    if(!r.ok) return false;
    state.result=d.payload;
    renderResults();
    document.getElementById('results').scrollIntoView({behavior:'instant',block:'start'});
    toast('Saved build loaded.');
    return true;
  }catch(e){ return false; }
}

async function loadConfig(){
  try{const r=await fetch(API_BASE + '/api/config');config=await r.json();}
  catch(e){toast('Offline demo mode — core UI still works.');config={countries:[{code:'US',name:'United States',currency:'USD'}],languages:[{code:'en',name:'English',native:'English',dir:'ltr'}],games:['Fortnite','Warzone','GTA V','Minecraft'],currencies:{USD:'$'},kofi:'https://ko-fi.com/simbawwyy00'}}
  const savedCountry=localStorage.getItem('byp_country');
  const savedLanguage=localStorage.getItem('byp_language');
  if(savedCountry && config.countries.some(x=>x.code===savedCountry)) state.country=savedCountry;
  const picked=config.countries.find(x=>x.code===state.country); if(picked) state.currency=picked.currency||state.currency;
  if(savedLanguage && config.languages.some(x=>x.code===savedLanguage)) state.language=savedLanguage;
  const lang=config.languages.find(x=>x.code===state.language)||config.languages[0];
  document.documentElement.lang=lang?.code||'en'; document.documentElement.dir=lang?.dir||'ltr';
  updateCountryUI();updateBudgetUI();renderGames();renderDocks();
}

async function loadExplore(){
  try{
    const r=await fetch(API_BASE + '/api/explore');
    if(!r.ok) return;
    const d=await r.json();
    el('statBuilds').textContent=Number(d.stats.builds||0).toLocaleString();
    el('statViews').textContent=Number(d.stats.views||0).toLocaleString();
    el('statShares').textContent=Number(d.stats.shares||0).toLocaleString();
    const items=[...(d.live||[]),...(d.curated||[])].slice(0,6);
    const box=el('exploreGrid');
    if(!items.length)return;
    box.innerHTML=items.map((x,i)=>{
      const label=x.label||((x.performance_fit||0)>93?'BEST FIT':'BUILD');
      const href=x.id&&x.id!=='reference-sweet-spot'&&x.id!=='reference-quiet'&&x.id!=='reference-fast'?`/build/${x.id}#results`:'#builder';
      const price=x.total!=null?fmtMoney(x.total,x.currency||state.currency):'—';
      return `<a class="explore-card ${i===0?'featured':''} reveal visible" href="${href}"><div class="explore-top"><span class="rank-pill ${i?'muted-pill':''}">${escapeHtml(label)}</span><span>${escapeHtml(x.type||'build')}</span></div><div class="abstract-rig ${i%2?'purple':'violet'}"><div class="abstract-box"></div><div class="abstract-line"></div><div class="abstract-node"></div></div><div class="explore-meta"><div><h3>${escapeHtml(x.title||'Shared build')}</h3><p>${x.views!=null?`${Number(x.views).toLocaleString()} views · ${Number(x.shares||0).toLocaleString()} shares`:'Reference build — starter example.'}</p></div><strong>${price}</strong></div></a>`;
    }).join('');
  }catch(e){/* visual fallback is intentional */}
}

function renderGames(){const box=el('gameTags');box.innerHTML='';config.games.slice(0,12).forEach(g=>{const b=document.createElement('button');b.className='tag'+(state.games.includes(g)?' selected':'');b.textContent=g;b.dataset.game=g;b.onclick=()=>{state.games=state.games.includes(g)?state.games.filter(x=>x!==g):[...state.games,g];renderGames();};box.appendChild(b)})}
function renderDocks(){renderLangList(config.languages);renderCountryList(config.countries)}
function renderLangList(list){const box=el('langList');box.innerHTML='';list.forEach(l=>{const b=document.createElement('button');b.className='dock-item'+(state.language===l.code?' active':'');b.innerHTML=`<strong>${l.native}</strong><small>${l.name}</small>`;b.onclick=()=>{state.language=l.code;localStorage.setItem('byp_language',l.code);document.documentElement.lang=l.code;document.documentElement.dir=l.dir||'ltr';updateCountryUI();closeDocks();toast(`Language set to ${l.native}`)};box.appendChild(b)})}
function renderCountryList(list){const box=el('countryList');box.innerHTML='';list.forEach(c=>{const b=document.createElement('button');b.className='dock-item'+(state.country===c.code?' active':'');b.innerHTML=`<strong>${c.name}</strong><small>${c.code} · ${c.currency}</small>`;b.onclick=()=>{state.country=c.code;state.currency=c.currency;localStorage.setItem('byp_country',c.code);updateCountryUI();updateBudgetUI();closeDocks();toast(`Market changed to ${c.name}`)};box.appendChild(b)})}
function openDock(which){el('overlay').hidden=false;el(which).hidden=false}
function closeDocks(){el('overlay').hidden=true;el('languageDock').hidden=true;el('countryDock').hidden=true}
function filterDock(inputId,list,render){const term=el(inputId).value.toLowerCase().trim();render(list.filter(x=>`${x.name} ${x.native||''} ${x.code||''}`.toLowerCase().includes(term)))}

function setStep(n){state.step=Math.max(1,Math.min(5,n));qa('.wizard-step').forEach(s=>s.classList.toggle('active',Number(s.dataset.step)===state.step));el('stepLabel').textContent=`Step ${state.step} of 5`;el('progressFill').style.width=`${state.step*20}%`;el('backBtn').disabled=state.step===1;el('wizardNote').textContent=state.step===2?'Budget is enough to start.':state.step<5?'Everything else is optional.':'Ready when you are.';window.scrollTo({top:document.getElementById('builder').offsetTop-70,behavior:'smooth'})}
function toggleChoice(elm){elm.classList.toggle('selected')}

qa('[data-device]').forEach(b=>b.onclick=()=>{qa('[data-device]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.device_type=b.dataset.device;if(state.device_type==='not_sure')toast('We’ll infer the best direction from your next answers.')})
qa('[data-goal]').forEach(b=>b.onclick=()=>{toggleChoice(b);state.use_cases=qa('[data-goal].selected').map(x=>x.dataset.goal)})
qa('[data-existing]').forEach(b=>b.onclick=()=>{b.classList.toggle('selected');state.existing_parts=qa('[data-existing].selected').map(x=>x.dataset.existing)})
qa('[data-pref]').forEach(b=>b.onclick=()=>{b.classList.toggle('selected');state.preferences=qa('[data-pref].selected').map(x=>x.dataset.pref)})
qa('[data-fps]').forEach(b=>b.onclick=()=>{qa('[data-fps]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.target_fps=Number(b.dataset.fps)})
qa('[data-res]').forEach(b=>b.onclick=()=>{qa('[data-res]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.resolution=b.dataset.res==='smart'?null:b.dataset.res})

el('budgetSlider').addEventListener('input',e=>{state.budget=Number(e.target.value);updateBudgetUI()});el('budgetInput').addEventListener('input',e=>{const v=Number(e.target.value)||0;state.budget=v;updateBudgetUI()});
el('nextBtn').onclick=()=>{if(state.step<5){setStep(state.step+1)}else runRecommendation()};el('backBtn').onclick=()=>setStep(state.step-1);el('skipStep').onclick=()=>state.step<5?setStep(state.step+1):runRecommendation();el('editBtn').onclick=()=>setStep(1);el('startBtn').onclick=()=>document.getElementById('builder').scrollIntoView({behavior:'smooth'});el('exploreBtn').onclick=()=>document.getElementById('explore').scrollIntoView({behavior:'smooth'});
el('langBtn').onclick=()=>openDock('languageDock');el('menuBtn')?.addEventListener('click',()=>{document.body.classList.toggle('menu-open')});el('countryBtn').onclick=()=>openDock('countryDock');el('overlay').onclick=closeDocks;qa('[data-close]').forEach(b=>b.onclick=closeDocks);el('langSearch').oninput=()=>filterDock('langSearch',config.languages,renderLangList);el('countrySearch').oninput=()=>filterDock('countrySearch',config.countries,renderCountryList);

function buildBrief(){const chips=[];chips.push(`${state.device_type==='not_sure'?'Flexible':state.device_type}`);if(state.games.length)chips.push(...state.games.slice(0,3));if(state.target_fps)chips.push(`${state.target_fps}+ FPS`);if(state.resolution)chips.push(state.resolution);if(state.use_cases.length)chips.push(...state.use_cases.slice(0,2));return chips}
async function runRecommendation(){
  if(!state.budget || state.budget<1){toast('Add a budget first.');setStep(2);return}
  const payload={...state};
  el('nextBtn').disabled=true;el('nextBtn').innerHTML='Matching <span>…</span>';
  try{const r=await fetch(API_BASE + '/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||'Could not build');state.result=data;state.preset='smart';renderResults();document.getElementById('results').scrollIntoView({behavior:'smooth'})}
  catch(e){toast(e.message||'Build failed.');}
  finally{el('nextBtn').disabled=false;el('nextBtn').innerHTML='Continue <span>→</span>'}
}
function renderResults(){
  const r=state.result;if(!r)return;el('summaryBudget').textContent=fmtMoney(r.query.budget,r.query.currency);el('summaryMarket').textContent=`${r.query.country} · ${r.query.currency}`;el('summaryDirection').textContent=r.title;
  el('briefChips').innerHTML=buildBrief().map(x=>`<span class="brief-chip">${escapeHtml(x)}</span>`).join('');
  renderResultPreset(r);
}
function renderResultPreset(result){const card=el('resultCard');card.innerHTML=`
  <div class="result-hero"><div><span class="section-kicker">MATCH READY</span><h3>${escapeHtml(result.title)}</h3><p>${escapeHtml(result.tagline)}</p><div class="result-metrics"><span>Value <b>${result.value_score}</b></span><span>Future <b>${result.future_score}</b></span>${result.fps_estimate?`<span>FPS est. <b>${result.fps_estimate.low}–${result.fps_estimate.high}</b></span>`:''}</div></div><div class="score-ring"><div><strong>${result.performance_fit}</strong><span>FIT</span></div></div></div>
  <div class="parts-grid">${result.parts.map(p=>`<div class="part-card"><div class="part-top"><span class="part-cat">${escapeHtml(p.category)}</span><span class="part-price">${fmtMoney(p.price,p.currency)}</span></div><h4>${escapeHtml(p.name)}</h4><p>${escapeHtml(p.why)}</p><div class="offers">${p.offers.slice(0,3).map(o=>{const live=!!o.live; const label=live?'LIVE':'REF'; const meta=o.captured_at?` · ${new Date(o.captured_at).toLocaleDateString()}`:''; return `<a class="offer-link" href="${o.url}" target="_blank" rel="noopener noreferrer${o.affiliate_ready?' sponsored':''}"><span class="offer-dot ${live?'on':''}"></span>${escapeHtml(o.store)} · ${fmtMoney(o.price,o.currency)} <small class="offer-source">${label}${meta}</small> →</a>`}).join('')}</div></div>`).join('')}</div>
  <div class="reason-strip">${result.reasons.slice(0,3).map((x,i)=>`<div class="reason-box"><strong>${['Why this fits','Goal check','Money move'][i]}</strong>${escapeHtml(x)}</div>`).join('')}</div>
  <div class="build-footer"><div><span class="muted">Estimated total</span><div class="build-total">${fmtMoney(result.total,result.currency)}</div><small id="dataModeNote" class="data-note"></small></div><div class="build-actions"><button class="small-btn" id="saveBuild">Save</button><button class="small-btn" id="shareBuild">Share</button><button class="small-btn" id="copyBuild">Copy link</button></div></div>`;
  qa('.preset-tab').forEach(x=>x.classList.remove('active'));const active=state.preset==='smart'?q('[data-preset="smart"]'):state.preset==='speed'?q('[data-preset="speed"]'):q('[data-preset="beast"]');active?.classList.add('active');
  el('heroFit').textContent=`${result.performance_fit}%`;el('heroBudget').textContent=fmtMoney(result.query.budget,result.query.currency);
  el('saveBuild').onclick=saveBuild;el('copyBuild').onclick=copyBuild;const shareBtn=el('shareBuild');if(shareBtn)shareBtn.onclick=shareBuild;const dataNote=el('dataModeNote');if(dataNote)dataNote.textContent=result.data_mode==='reference-demo'?'Reference catalog — verify prices before buying.':'Fresh live offers are active where available; reference prices remain clearly labeled.';
}
qa('.preset-tab').forEach(b=>b.onclick=()=>{state.preset=b.dataset.preset;const idx=b.dataset.preset==='smart'?0:b.dataset.preset==='speed'?1:2;renderResultPreset(state.result.alternatives[idx]||state.result)});
qa('[data-whatif]').forEach(b=>b.onclick=()=>{if(!state.result)return;const w=b.dataset.whatif;if(w==='500'){const delta=Math.max(50,Math.round(state.budget*0.07));state.budget+=delta;updateBudgetUI();toast(`Budget lifted by ${fmtMoney(delta)} — rerunning the match.`);runRecommendation()}else if(w==='fps'){state.target_fps=Math.max(144,Number(state.target_fps||60)+60);toast(`Target raised to ${state.target_fps}+ FPS.`);runRecommendation()}else if(w==='quiet'){if(!state.preferences.includes('Quiet'))state.preferences.push('Quiet');toast('Quietness is now prioritized.');runRecommendation()}else if(w==='future'){if(!state.preferences.includes('Future-proof'))state.preferences.push('Future-proof');toast('Future-proofing is now prioritized.');runRecommendation()}})

async function saveBuild(){if(!state.result)return;try{const r=await fetch(API_BASE + '/api/builds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.result)});const d=await r.json();const url=`${location.origin}${d.url}`;history.replaceState({},'',d.url);await navigator.clipboard?.writeText(url);toast('Build saved — link copied.')}catch(e){toast('Could not save the build.')}}
async function copyBuild(){const url=location.href.includes('/build/')?location.href:location.href.split('#')[0]+'#results';try{await navigator.clipboard.writeText(url);toast('Link copied.')}catch(e){toast(url)}}
async function shareBuild(){
  if(!state.result)return;
  try{
    const save=await fetch(API_BASE+'/api/builds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.result)});
    const d=await save.json();
    const url=location.origin+d.url;
    history.replaceState({},'',d.url);
    try{await fetch(API_BASE+`/api/builds/${d.id}/share`,{method:'POST'})}catch{}
    if(navigator.share){await navigator.share({title:'My BuildYourPC build',text:'I found this build on BuildYourPC.',url});}
    else{await navigator.clipboard?.writeText(url);toast('Share link copied.');}
  }catch{toast('Could not create a share link.');}
}

function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}

const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')}),{threshold:.12});qa('.reveal').forEach(x=>observer.observe(x));

window.addEventListener('hashchange',()=>{if(location.hash==='#results')document.getElementById('results').scrollIntoView({behavior:'smooth'})});
loadConfig().then(()=>{loadExistingBuild();loadExplore();});
