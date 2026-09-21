const viewer = document.querySelector('#viewer');
const views = {
  overview: {orbit:'-25deg 72deg 105%', target:'auto auto auto', fov:'30deg'},
  working: {orbit:'-30deg 38deg 2.8m', target:'0m 1.02m 0.05m', fov:'30deg'},
  console: {orbit:'-8deg 55deg 2.5m', target:'0m 0.64m 0.96m', fov:'30deg'}
};
function setView(name) {
  const view = views[name];
  viewer.cameraOrbit = view.orbit; viewer.cameraTarget = view.target; viewer.fieldOfView = view.fov;
  document.querySelectorAll('[data-view]').forEach(b=>{const on=b.dataset.view===name;b.classList.toggle('active',on);b.setAttribute('aria-pressed',on);});
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) viewer.jumpCameraToGoal?.();
}
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
document.querySelector('#reset').addEventListener('click',()=>setView('overview'));
viewer.addEventListener('progress', e=>{const p=Math.round(e.detail.totalProgress*100);document.querySelector('#progress').style.width=`${p}%`;document.querySelector('#loading-label').textContent=p<100?`Loading machine · ${p}%`:'Preparing your 3D view…';});
viewer.addEventListener('load',()=>{document.querySelector('.viewer-wrap').classList.add('loaded');document.querySelector('.viewer-error').hidden=true;});
viewer.addEventListener('error',()=>{document.querySelector('.viewer-error').hidden=false;});
document.querySelector('#retry').addEventListener('click',()=>{document.querySelector('.viewer-error').hidden=true;viewer.src=`assets/micro-mlp42.glb?retry=${Date.now()}`;});
