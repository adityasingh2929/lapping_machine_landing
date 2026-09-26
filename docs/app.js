const viewer = document.querySelector('#viewer');
const machines = {
  original: {src:'assets/micro-mlp42.glb',poster:'assets/machine-poster.png',name:'Machine 1 — Micro MLP 42'},
  blue: {src:'assets/micro-blue.glb',poster:'assets/blue-poster.png',name:'Machine 2 — Blue Micro lapping machine'}
};
let currentMachine = 'original';
const copy = {
  eyebrow: document.querySelector('.hero-copy .eyebrow').innerHTML,
  intro: document.querySelector('.intro').textContent,
  strip: document.querySelector('.spec-strip').innerHTML,
  details: document.querySelector('.detail-grid').innerHTML,
  specs: document.querySelector('.specifications dl').innerHTML,
  specNote: document.querySelector('.specifications p:not(.eyebrow)').textContent
};
const views = {
  overview: {orbit:'-25deg 72deg 105%', target:'auto auto auto', fov:'30deg'},
  working: {orbit:'-30deg 38deg 2.8m', target:'0m 1.02m 0.05m', fov:'30deg'},
  console: {orbit:'-8deg 55deg 2.5m', target:'0m 0.64m 0.96m', fov:'30deg'}
};
function setView(name) {
  const view = views[name];
  viewer.setAttribute('camera-orbit',view.orbit); viewer.setAttribute('camera-target',view.target); viewer.setAttribute('field-of-view',view.fov);
  document.querySelectorAll('[data-view]').forEach(b=>{const on=b.dataset.view===name;b.classList.toggle('active',on);b.setAttribute('aria-pressed',on);});
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) viewer.jumpCameraToGoal?.();
}
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
document.querySelector('#reset').addEventListener('click',()=>setView('overview'));
viewer.addEventListener('progress', e=>{const p=Math.round(e.detail.totalProgress*100);document.querySelector('#progress').style.width=`${p}%`;document.querySelector('#loading-label').textContent=p<100?`Loading machine · ${p}%`:'Preparing your 3D view…';});
viewer.addEventListener('load',()=>{document.querySelector('.viewer-wrap').classList.add('loaded');document.querySelector('.viewer-error').hidden=true;});
viewer.addEventListener('error',()=>{document.querySelector('.viewer-error').hidden=false;});
document.querySelector('#retry').addEventListener('click',()=>{document.querySelector('.viewer-error').hidden=true;viewer.setAttribute('src',`${machines[currentMachine].src}?retry=${Date.now()}`);});
function chooseMachine(key,updateURL=true) {
  if (!machines[key]) return;
  const machine=machines[key];currentMachine=key;
  document.querySelectorAll('[data-machine]').forEach(button=>{
    const active=button.dataset.machine===key;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));
  });
  document.querySelector('.viewer-wrap').classList.remove('loaded');
  document.querySelector('.viewer-error').hidden=true;
  document.querySelector('#progress').style.width='0%';
  document.querySelector('#loading-label').textContent=`Loading ${machine.name}…`;
  viewer.setAttribute('poster',machine.poster);
  viewer.setAttribute('alt',`${machine.name}. Drag or use arrow keys to rotate; scroll or pinch to zoom.`);
  const poster=document.querySelector('.poster-button img');poster.src=machine.poster;poster.alt=machine.name;
  document.querySelector('.poster-button').setAttribute('aria-label',`Load ${machine.name} in 3D`);
  viewer.setAttribute('src',machine.src);setView('overview');
  const blue=key==='blue';
  document.querySelector('#hero-title').innerHTML=blue?'Machine <em>2.</em>':'Machine <em>1.</em>';
  document.querySelector('.viewer-watermark').textContent=blue?'MICRO':'MLP 42';
  document.querySelector('.hero-copy .eyebrow').innerHTML=blue?'<span></span> MACHINE 2 / MICRO':copy.eyebrow;
  document.querySelector('.intro').textContent=blue?'Explore the blue Micro lapping machine, with three working stations, a silver working surface and air controls mounted at the operator’s side.':copy.intro;
  document.querySelector('.spec-strip').innerHTML=blue?'<div><span>MACHINE</span><strong>Machine 2</strong></div><div><span>WORKING STATIONS</span><strong>3</strong></div><div><span>FINISH</span><strong>RAL <small>5002</small></strong></div><div><span>CONTROLS</span><strong>Pneumatic</strong></div><p>Explore a different<br><b>machine configuration.</b></p>':copy.strip;
  const cards=[
    ['blue-working.png','Three plain slotted rings over a continuous silver working plate','The working assembly','Three slotted rings sit on a shared working surface beneath thin, raised pressure discs.'],
    ['blue-controls.png','Gauge, filter and lubricator mounted below the front Micro nameplate','Air controls up front','The filter, regulator and lubricator face the operator, with the connected air line routed back to the machine.'],
    ['blue-poster.png','Blue machine with its ivory control face and blue console','The blue machine','Ultramarine panels, a pale blue-grey frame and an ivory control face distinguish this machine.']
  ];
  document.querySelector('.detail-grid').innerHTML=blue?cards.map(([src,alt,title,text],i)=>`<article class="detail-card"><div class="detail-image"><img src="assets/${src}" alt="${alt}" width="900" height="700" loading="lazy"></div><div class="detail-copy"><span>0${i+1}</span><h3>${title}</h3><p>${text}</p></div></article>`).join(''):copy.details;
  document.querySelector('.specifications p:not(.eyebrow)').textContent=blue?'Configuration shown for the blue machine. Contact us for its electrical and production specifications.':copy.specNote;
  document.querySelector('.specifications dl').innerHTML=blue?[['Manufacturer','Amardeep Enterprise'],['Machine','Micro Lapping Machine'],['Configuration','Blue machine'],['Working stations','3'],['Panel finish','RAL 5002 blue'],['Frame','Pale blue-grey'],['Air controls','Front, operator-facing']].map(([label,value])=>`<div><dt>${label}</dt><dd>${value}</dd></div>`).join(''):copy.specs;
  if(updateURL){const url=new URL(location.href);url.searchParams.set('machine',key);history.replaceState(null,'',url);}
}
document.querySelectorAll('[data-machine]').forEach(button=>button.addEventListener('click',()=>chooseMachine(button.dataset.machine)));
const initialMachine=new URL(location.href).searchParams.get('machine');
if(initialMachine==='blue')chooseMachine('blue',false);
