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
let busyActions = new Set();

const TRANSLATIONS = {
  en: {
    continue: 'Continue', matching: 'Matching', addBudget: 'Add a budget first.', buildFailed: 'Build failed. Please try again.',
    saved: 'Build saved — link copied.', saveFailed: 'Could not save the build.', shareFailed: 'Could not create a share link.',
    linkCopied: 'Link copied.', languageSet: 'Language set to', marketChanged: 'Market changed to',
    offline: 'Could not reach the API. Please check your connection and try again.',
    genericError: 'Unable to complete this action. Please try again.', budgetRange: 'Budget must be within the allowed range.',
    matchReady: 'Match ready', smart: 'Smart Buy', speed: 'Speed Demon', beast: 'The Beast', estimatedTotal: 'Estimated total',
    whyFits: 'Why this fits', goalCheck: 'Goal check', moneyMove: 'Money move', save: 'Save', share: 'Share', copy: 'Copy link',
    referenceNote: 'Reference catalog — verify prices before buying.', liveNote: 'Fresh live offers are active where available; reference prices remain clearly labeled.'
  },
  fr: {
    continue: 'Continuer', matching: 'Recherche', addBudget: 'Ajoutez d’abord un budget.', buildFailed: 'Échec de la configuration. Réessayez.',
    saved: 'Configuration enregistrée — lien copié.', saveFailed: 'Impossible d’enregistrer la configuration.', shareFailed: 'Impossible de créer le lien de partage.',
    linkCopied: 'Lien copié.', languageSet: 'Langue définie sur', marketChanged: 'Marché défini sur',
    offline: 'Impossible de joindre l’API. Vérifiez votre connexion puis réessayez.',
    genericError: 'Impossible de terminer cette action. Réessayez.', budgetRange: 'Le budget doit respecter la plage autorisée.',
    matchReady: 'Résultat prêt', smart: 'Achat intelligent', speed: 'Performance', beast: 'Le monstre', estimatedTotal: 'Total estimé',
    whyFits: 'Pourquoi ce choix', goalCheck: 'Vérification', moneyMove: 'Budget', save: 'Enregistrer', share: 'Partager', copy: 'Copier le lien',
    referenceNote: 'Catalogue de référence — vérifiez les prix avant achat.', liveNote: 'Les offres en direct sont utilisées lorsqu’elles sont disponibles; les prix de référence restent identifiés.'
  },
  ar: {
    continue: 'متابعة', matching: 'جاري المطابقة', addBudget: 'أدخل الميزانية أولًا.', buildFailed: 'تعذر إنشاء التجميعة. حاول مرة أخرى.',
    saved: 'تم حفظ التجميعة — تم نسخ الرابط.', saveFailed: 'تعذر حفظ التجميعة.', shareFailed: 'تعذر إنشاء رابط المشاركة.',
    linkCopied: 'تم نسخ الرابط.', languageSet: 'تم اختيار اللغة', marketChanged: 'تم اختيار السوق',
    offline: 'تعذر الاتصال بالخادم. تحقق من اتصالك وحاول مرة أخرى.',
    genericError: 'تعذر تنفيذ العملية. حاول مرة أخرى.', budgetRange: 'الميزانية خارج النطاق المسموح.',
    matchReady: 'النتيجة جاهزة', smart: 'الاختيار الذكي', speed: 'الأداء', beast: 'الأقوى', estimatedTotal: 'الإجمالي المتوقع',
    whyFits: 'لماذا يناسبك', goalCheck: 'تحقق من الهدف', moneyMove: 'قرار الميزانية', save: 'حفظ', share: 'مشاركة', copy: 'نسخ الرابط',
    referenceNote: 'بيانات مرجعية — تحقق من الأسعار قبل الشراء.', liveNote: 'تظهر الأسعار الحية عند توفرها، وتبقى الأسعار المرجعية موضحة بوضوح.'
  }
};

function t(key){return (TRANSLATIONS[state.language]||TRANSLATIONS.en)[key]||TRANSLATIONS.en[key]||key}
function toast(msg){const node=el('toast');node.textContent=msg;node.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(()=>node.classList.remove('show'),2500)}
function currencyConfig(code){return config.currencies?.[String(code||'USD').toUpperCase()]||config.currencies?.USD||{symbol:String(code||'USD'),locale:undefined,decimalDigits:0,minimum:0,maximum:10000}}
function currencySymbol(code){return currencyConfig(code).symbol || code}
function fmtMoney(value, code=state.currency){
  const cfg=currencyConfig(code); const n=Number(value); if(!Number.isFinite(n)) return '—';
  try{return new Intl.NumberFormat(cfg.locale||navigator.language,{style:'currency',currency:code,minimumFractionDigits:Number(cfg.decimalDigits??0),maximumFractionDigits:Number(cfg.decimalDigits??0)}).format(n)}catch{return `${currencySymbol(code)}${Math.round(n).toLocaleString()}`}
}
function countryName(code){return config.countries.find(x=>x.code===code)?.name || code}
function updateCountryUI(){el('countryLabel').textContent=state.country;el('budgetCurrency').textContent=state.currency;el('currencySymbol').textContent=currencySymbol(state.currency);el('langBtn').textContent=(config.languages.find(x=>x.code===state.language)?.code||'en').toUpperCase();}
function updateBudgetUI(){const cfg=currencyConfig(state.currency);const min=Number(cfg.minimum||150), max=Number(cfg.maximum||10000);state.budget=Math.min(max,Math.max(min,Number(state.budget)||min));el('budgetInput').min=min;el('budgetInput').max=max;el('budgetInput').step=Number(cfg.decimalDigits||0)>0?'0.01':'1';el('budgetInput').value=Number(state.budget).toLocaleString(undefined,{maximumFractionDigits:Number(cfg.decimalDigits||0)});el('budgetSlider').min=min;el('budgetSlider').max=max;el('budgetSlider').step=Math.max(1,Math.round((max-min)/250));el('budgetSlider').value=Math.min(max,Math.max(min,state.budget));el('heroBudget').textContent=fmtMoney(state.budget);const extra=Math.max(1,Math.round(state.budget*0.07));const title=el('whatIfBudgetTitle');if(title)title.textContent=`${t('smart')}: ${fmtMoney(extra)}`;}

async function readResponse(r){
  const type=(r.headers.get('content-type')||'').toLowerCase();
  const raw=await r.text();
  let data=null;
  if(raw.trim()){
    if(type.includes('application/json') || /^[\[{]/.test(raw.trim())){try{data=JSON.parse(raw)}catch{} }
  }
  if(!r.ok){
    const message=data?.error?.message||data?.error||data?.message||(`${r.status} ${r.statusText}`.trim())||t('genericError');
    const err=new Error(message);err.status=r.status;err.code=data?.error?.code||'HTTP_ERROR';throw err;
  }
  if(!raw.trim()) return {};
  if(data===null){const err=new Error(t('genericError'));err.code='INVALID_JSON_RESPONSE';throw err;}
  return data;
}
async function apiFetch(path, options={}){
  let r; try{r=await fetch(API_BASE+path,{...options,headers:{Accept:'application/json',...(options.headers||{})}})}catch(e){const err=new Error(t('offline'));err.code='NETWORK_ERROR';throw err}
  return readResponse(r);
}
function applyTranslations(){
  const L={
    '#startBtn':{text:'Start building'}, '#exploreBtn':{text:'Explore builds'}, '#tipBtn':{text:'Support'},
    '#backBtn':{text:'← Back'}, '#nextBtn':{text:t('continue')+' →'}, '#editBtn':{text:'Edit'},
    '.result-title':{text:t('matchReady')}, '[data-preset="smart"]':{text:'🧠 '+t('smart')}, '[data-preset="speed"]':{text:'⚡ '+t('speed')}, '[data-preset="beast"]':{text:'👑 '+t('beast')}
  };
  Object.entries(L).forEach(([sel,cfg])=>{const n=q(sel);if(n&&cfg.text)n.textContent=cfg.text});
  qa('.language-dock .section-kicker').forEach(n=>n.textContent='LANGUAGE');
  const search=el('langSearch');if(search)search.placeholder=state.language==='ar'?'ابحث عن لغة…':state.language==='fr'?'Rechercher une langue…':'Search language…';
  const csearch=el('countrySearch');if(csearch)csearch.placeholder=state.language==='ar'?'ابحث عن دولة…':state.language==='fr'?'Rechercher un pays…':'Search country…';
}

async function loadExistingBuild(){
  const m=location.pathname.match(/^\/build\/([A-Za-z0-9_-]+)$/);
  if(!m) return false;
  try{
    const d=await apiFetch(`/api/builds/${m[1]}`);
    state.result=d.payload;
    renderResults();
    document.getElementById('results').scrollIntoView({behavior:'instant',block:'start'});
    toast(state.language==='ar'?'تم تحميل التجميعة المحفوظة.':state.language==='fr'?'Configuration enregistrée chargée.':'Saved build loaded.');
    return true;
  }catch(e){ console.warn('saved build load failed',e); return false; }
}

async function loadConfig(){
  try{config=await apiFetch('/api/config');}
  catch(e){toast(e.message);config={countries:[{code:'US',name:'United States',currency:'USD'}],languages:[{code:'en',name:'English',native:'English',dir:'ltr'}],games:['Fortnite','Warzone','GTA V','Minecraft'],currencies:{USD:{symbol:'$',locale:'en-US',decimalDigits:0,minimum:150,maximum:10000}},kofi:'https://ko-fi.com/simbawwyy00'}}
  const savedCountry=localStorage.getItem('byp_country');
  const savedLanguage=localStorage.getItem('byp_language');
  if(savedCountry && config.countries.some(x=>x.code===savedCountry)) state.country=savedCountry;
  const picked=config.countries.find(x=>x.code===state.country); if(picked) state.currency=picked.currency||state.currency;
  if(savedLanguage && config.languages.some(x=>x.code===savedLanguage)) state.language=savedLanguage;
  const lang=config.languages.find(x=>x.code===state.language)||config.languages[0];
  document.documentElement.lang=lang?.code||'en'; document.documentElement.dir=lang?.dir||'ltr';
  updateCountryUI();updateBudgetUI();applyTranslations();renderGames();renderDocks();
}

async function loadExplore(){
  try{
    const d=await apiFetch('/api/explore');
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
  }catch(e){ console.warn('explore load failed',e); }
}

function renderGames(){const box=el('gameTags');box.innerHTML='';config.games.slice(0,12).forEach(g=>{const b=document.createElement('button');b.className='tag'+(state.games.includes(g)?' selected':'');b.textContent=g;b.dataset.game=g;b.onclick=()=>{state.games=state.games.includes(g)?state.games.filter(x=>x!==g):[...state.games,g];renderGames();};box.appendChild(b)})}
function renderDocks(){renderLangList(config.languages);renderCountryList(config.countries)}
function renderLangList(list){const box=el('langList');box.innerHTML='';list.forEach(l=>{const b=document.createElement('button');b.className='dock-item'+(state.language===l.code?' active':'');b.innerHTML=`<strong>${escapeHtml(l.native)}</strong><small>${escapeHtml(l.name)}</small>`;b.onclick=()=>{state.language=l.code;localStorage.setItem('byp_language',l.code);document.documentElement.lang=l.code;document.documentElement.dir=l.dir||'ltr';applyTranslations();updateCountryUI();renderLangList(config.languages);closeDocks();toast(`${t('languageSet')} ${l.native}`);};box.appendChild(b)})}
function renderCountryList(list){const box=el('countryList');box.innerHTML='';list.forEach(c=>{const b=document.createElement('button');b.className='dock-item'+(state.country===c.code?' active':'');b.innerHTML=`<strong>${c.name}</strong><small>${c.code} · ${c.currency}</small>`;b.onclick=()=>{state.country=c.code;state.currency=c.currency;localStorage.setItem('byp_country',c.code);updateCountryUI();updateBudgetUI();closeDocks();toast(`${t('marketChanged')} ${c.name}`)};box.appendChild(b)})}
function openDock(which){el('overlay').hidden=false;el(which).hidden=false}
function closeDocks(){el('overlay').hidden=true;el('languageDock').hidden=true;el('countryDock').hidden=true}
function filterDock(inputId,list,render){const term=el(inputId).value.toLowerCase().trim();render(list.filter(x=>`${x.name} ${x.native||''} ${x.code||''}`.toLowerCase().includes(term)))}

function setStep(n){state.step=Math.max(1,Math.min(5,n));qa('.wizard-step').forEach(s=>s.classList.toggle('active',Number(s.dataset.step)===state.step));el('stepLabel').textContent=`Step ${state.step} of 5`;el('progressFill').style.width=`${state.step*20}%`;el('backBtn').disabled=state.step===1;el('wizardNote').textContent=state.step===2?'Budget is enough to start.':state.step<5?'Everything else is optional.':'Ready when you are.';window.scrollTo({top:document.getElementById('builder').offsetTop-70,behavior:'smooth'})}
function toggleChoice(elm){elm.classList.toggle('selected')}

qa('[data-device]').forEach(b=>b.onclick=()=>{qa('[data-device]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.device_type=b.dataset.device;if(state.device_type==='not_sure')toast(state.language==='ar'?'سنحدد الاتجاه الأنسب من إجاباتك التالية.':state.language==='fr'?'Nous déterminerons la meilleure direction avec vos prochaines réponses.':'We’ll infer the best direction from your next answers.')})
qa('[data-goal]').forEach(b=>b.onclick=()=>{toggleChoice(b);state.use_cases=qa('[data-goal].selected').map(x=>x.dataset.goal)})
qa('[data-existing]').forEach(b=>b.onclick=()=>{b.classList.toggle('selected');state.existing_parts=qa('[data-existing].selected').map(x=>x.dataset.existing)})
qa('[data-pref]').forEach(b=>b.onclick=()=>{b.classList.toggle('selected');state.preferences=qa('[data-pref].selected').map(x=>x.dataset.pref)})
qa('[data-fps]').forEach(b=>b.onclick=()=>{qa('[data-fps]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.target_fps=Number(b.dataset.fps)})
qa('[data-res]').forEach(b=>b.onclick=()=>{qa('[data-res]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.resolution=b.dataset.res==='smart'?null:b.dataset.res})

el('budgetSlider').addEventListener('input',e=>{state.budget=Number(e.target.value);updateBudgetUI()});el('budgetInput').addEventListener('input',e=>{const raw=e.target.value.replace(/,/g,'');const v=Number(raw);if(Number.isFinite(v))state.budget=v;});el('budgetInput').addEventListener('blur',updateBudgetUI);
el('nextBtn').onclick=()=>{if(state.step<5){setStep(state.step+1)}else runRecommendation()};el('backBtn').onclick=()=>setStep(state.step-1);el('skipStep').onclick=()=>state.step<5?setStep(state.step+1):runRecommendation();el('editBtn').onclick=()=>setStep(1);el('startBtn').onclick=()=>document.getElementById('builder').scrollIntoView({behavior:'smooth'});el('exploreBtn').onclick=()=>document.getElementById('explore').scrollIntoView({behavior:'smooth'});
el('langBtn').onclick=()=>openDock('languageDock');el('menuBtn')?.addEventListener('click',()=>{document.body.classList.toggle('menu-open')});el('countryBtn').onclick=()=>openDock('countryDock');el('overlay').onclick=closeDocks;qa('[data-close]').forEach(b=>b.onclick=closeDocks);el('langSearch').oninput=()=>filterDock('langSearch',config.languages,renderLangList);el('countrySearch').oninput=()=>filterDock('countrySearch',config.countries,renderCountryList);

function buildBrief(){const chips=[];chips.push(`${state.device_type==='not_sure'?'Flexible':state.device_type}`);if(state.games.length)chips.push(...state.games.slice(0,3));if(state.target_fps)chips.push(`${state.target_fps}+ FPS`);if(state.resolution)chips.push(state.resolution);if(state.use_cases.length)chips.push(...state.use_cases.slice(0,2));return chips}
async function runRecommendation(){
  const cfg=currencyConfig(state.currency), min=Number(cfg.minimum||150), max=Number(cfg.maximum||10000);
  if(!Number.isFinite(Number(state.budget)) || state.budget<min || state.budget>max){toast(`${t('budgetRange')} ${fmtMoney(min,state.currency)} – ${fmtMoney(max,state.currency)}`);setStep(2);return}
  if(busyActions.has('recommend')) return;
  busyActions.add('recommend'); const btn=el('nextBtn'); btn.disabled=true; btn.innerHTML=t('matching')+' <span>…</span>';
  try{state.result=await apiFetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...state,budget:Number(state.budget),currency:state.currency,country:state.country})});state.preset='smart';renderResults();document.getElementById('results').scrollIntoView({behavior:'smooth'});}
  catch(e){console.error('recommend failed',e);toast(e.message||t('buildFailed'));}
  finally{busyActions.delete('recommend');btn.disabled=false;btn.innerHTML=t('continue')+' <span>→</span>';}
}

function renderResults(){
  const r=state.result;if(!r||!r.query)return;el('summaryBudget').textContent=fmtMoney(r.query.budget,r.query.currency);el('summaryMarket').textContent=`${r.query.country} · ${r.query.currency}`;el('summaryDirection').textContent=r.title;
  el('briefChips').innerHTML=buildBrief().map(x=>`<span class="brief-chip">${escapeHtml(x)}</span>`).join('');
  renderResultPreset(r);
}
function renderResultPreset(result){const card=el('resultCard');card.innerHTML=`
  <div class="result-hero"><div><span class="section-kicker">${t('matchReady')}</span><h3>${escapeHtml(result.title)}</h3><p>${escapeHtml(result.tagline)}</p><div class="result-metrics"><span>Value <b>${result.value_score}</b></span><span>Future <b>${result.future_score}</b></span>${result.fps_estimate?`<span>FPS est. <b>${result.fps_estimate.low}–${result.fps_estimate.high}</b></span>`:''}</div></div><div class="score-ring"><div><strong>${result.performance_fit}</strong><span>FIT</span></div></div></div>
  <div class="parts-grid">${(result.parts||[]).map(p=>`<div class="part-card"><div class="part-top"><span class="part-cat">${escapeHtml(p.category)}</span><span class="part-price">${fmtMoney(p.price,p.currency)}</span></div><h4>${escapeHtml(p.name)}</h4><p>${escapeHtml(p.why)}</p><div class="offers">${(p.offers||[]).slice(0,3).map(o=>{const live=!!o.live; const label=live?'LIVE':'REF'; const meta=o.captured_at?` · ${new Date(o.captured_at).toLocaleDateString()}`:''; return `<a class="offer-link" href="${o.url}" target="_blank" rel="noopener noreferrer${o.affiliate_ready?' sponsored':''}"><span class="offer-dot ${live?'on':''}"></span>${escapeHtml(o.store)} · ${fmtMoney(o.price,o.currency)} <small class="offer-source">${label}${meta}</small> →</a>`}).join('')}</div></div>`).join('')}</div>
  <div class="reason-strip">${(result.reasons||[]).slice(0,3).map((x,i)=>`<div class="reason-box"><strong>${[t('whyFits'),t('goalCheck'),t('moneyMove')][i]}</strong>${escapeHtml(x)}</div>`).join('')}</div>
  <div class="build-footer"><div><span class="muted">${t('estimatedTotal')}</span><div class="build-total">${fmtMoney(result.total,result.currency)}</div><small id="dataModeNote" class="data-note"></small></div><div class="build-actions"><button class="small-btn" id="saveBuild">${t('save')}</button><button class="small-btn" id="shareBuild">${t('share')}</button><button class="small-btn" id="copyBuild">${t('copy')}</button></div></div>`;
  qa('.preset-tab').forEach(x=>x.classList.remove('active'));const active=state.preset==='smart'?q('[data-preset="smart"]'):state.preset==='speed'?q('[data-preset="speed"]'):q('[data-preset="beast"]');active?.classList.add('active');
  el('heroFit').textContent=`${result.performance_fit}%`;el('heroBudget').textContent=fmtMoney(result.query.budget,result.query.currency);
  el('saveBuild').onclick=saveBuild;el('copyBuild').onclick=copyBuild;const shareBtn=el('shareBuild');if(shareBtn)shareBtn.onclick=shareBuild;const dataNote=el('dataModeNote');if(dataNote)dataNote.textContent=result.data_mode==='reference-demo'?t('referenceNote'):t('liveNote');
}
qa('.preset-tab').forEach(b=>b.onclick=()=>{state.preset=b.dataset.preset;const idx=b.dataset.preset==='smart'?0:b.dataset.preset==='speed'?1:2;renderResultPreset(state.result.alternatives[idx]||state.result)});
qa('[data-whatif]').forEach(b=>b.onclick=()=>{if(!state.result)return;const w=b.dataset.whatif;if(w==='500'){const delta=Math.max(50,Math.round(state.budget*0.07));state.budget+=delta;updateBudgetUI();toast(`Budget lifted by ${fmtMoney(delta)} — rerunning the match.`);runRecommendation()}else if(w==='fps'){state.target_fps=Math.max(144,Number(state.target_fps||60)+60);toast(`Target raised to ${state.target_fps}+ FPS.`);runRecommendation()}else if(w==='quiet'){if(!state.preferences.includes('Quiet'))state.preferences.push('Quiet');toast('Quietness is now prioritized.');runRecommendation()}else if(w==='future'){if(!state.preferences.includes('Future-proof'))state.preferences.push('Future-proof');toast('Future-proofing is now prioritized.');runRecommendation()}})

async function saveBuild(){
  if(!state.result||busyActions.has('save'))return; busyActions.add('save'); const b=el('saveBuild'); if(b)b.disabled=true;
  try{const d=await apiFetch('/api/builds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.result)});const url=`${location.origin}${d.url}`;history.replaceState({},'',d.url);try{await navigator.clipboard?.writeText(url)}catch{}toast(t('saved'));}
  catch(e){console.error('save failed',e);toast(e.message||t('saveFailed'));} finally{busyActions.delete('save');if(b)b.disabled=false;}
}
async function copyBuild(){const url=location.href.includes('/build/')?location.href:location.href.split('#')[0]+'#results';try{await navigator.clipboard.writeText(url);toast(t('linkCopied'));}catch(e){toast(url)}}
async function shareBuild(){
  if(!state.result||busyActions.has('share'))return;busyActions.add('share');const b=el('shareBuild');if(b)b.disabled=true;
  try{const d=await apiFetch('/api/builds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.result)});const url=location.origin+d.url;history.replaceState({},'',d.url);try{await apiFetch(`/api/builds/${d.id}/share`,{method:'POST'});}catch(e){console.warn('share metric failed',e)}if(navigator.share)await navigator.share({title:'My BuildYourPC build',text:'I found this build on BuildYourPC.',url});else{await navigator.clipboard?.writeText(url);toast(t('linkCopied'));}}
  catch(e){console.error('share failed',e);if(e.name!=='AbortError')toast(e.message||t('shareFailed'));}
  finally{busyActions.delete('share');if(b)b.disabled=false;}
}

function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}

const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')}),{threshold:.12});qa('.reveal').forEach(x=>observer.observe(x));

window.addEventListener('hashchange',()=>{if(location.hash==='#results')document.getElementById('results').scrollIntoView({behavior:'smooth'})});
loadConfig().then(()=>{applyTranslations();loadExistingBuild();loadExplore();});
