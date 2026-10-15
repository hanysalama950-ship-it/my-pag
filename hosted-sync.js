'use strict';
(() => {
 const fmt=v=>v&&Number.isFinite(Date.parse(v))?new Intl.DateTimeFormat('ar-SA-u-ca-gregory-nu-latn',{dateStyle:'short',timeStyle:'short',timeZone:'Asia/Riyadh'}).format(new Date(v)):'غير متاح';
 const old=v=>!v||!Number.isFinite(Date.parse(v))||Date.now()-Date.parse(v)>3600000;
 let busy=false;
 const display=(offline=false)=>{
  const sources=D.sources||[],failed=sources.filter(s=>s.syncStatus==='error'),stale=sources.filter(s=>old(s.lastSuccessAt));
  const box=document.getElementById('freshness');box.classList.toggle('warning',offline||failed.length>0||stale.length>0);
  box.textContent='آخر فحص للمصادر: '+fmt(D.sync?.checkedAt||D.fetchedAt)+'. '+(offline?'تعذر فحص النسخة المنشورة؛ المعروض آخر نسخة محفوظة. ':'الصفحة تفحص وجود نسخة منشورة جديدة كل دقيقة. ')+(failed.length?'تعذر تحديث '+failed.length+' مصادر. ':'')+(stale.length?stale.length+' مصادر تجاوزت ساعة منذ آخر قراءة ناجحة. ':'')+'تاريخ كل مصدر في قسم المصادر. سحب المصادر يعتمد على تشغيل الجهاز والتطبيق؛ تحديث الصفحة لا يعني تحديث جميع المصادر.';
  document.getElementById('sidebarDate').textContent='آخر فحص: '+fmt(D.sync?.checkedAt||D.fetchedAt);
  const label=document.querySelector('.private-label');if(label)label.textContent='لوحة خاصة';
 };
 const original=renderSources;
 renderSources=function(){original();document.querySelectorAll('.sourcecard').forEach((card,i)=>{
  const s=D.sources[i];if(!s)return;const p=document.createElement('p');p.className='scope-note';
  p.textContent=(s.syncStatus==='error'?'تعذر التحديث':old(s.lastSuccessAt)?'بيانات تحتاج تحديثًا':s.syncStatus==='partial'?'قراءة جزئية ضمن النطاق المعلن':'قراءة ناجحة')+' · آخر نجاح: '+fmt(s.lastSuccessAt)+' · آخر محاولة: '+fmt(s.lastCheckedAt)+(s.syncError?' · '+s.syncError:'');card.appendChild(p);
 });};
 async function check(){
  if(busy||location.protocol==='file:')return;busy=true;
  try{
   const response=await fetch('./version.json?t='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(10000)});
   if(!response.ok)throw Error('Version unavailable');const v=await response.json();if(!/^[a-f0-9]{64}$/.test(v.revision))throw Error('Invalid version');
   if(v.revision!==window.CEO_RELEASE){
    try{sessionStorage.setItem('ceo-view',state.view);sessionStorage.setItem('ceo-project',selectedProject||'');}catch{}
    const url=new URL(location.href);url.searchParams.set('release',v.revision);location.replace(url.href);return;
   }display(false);
  }catch{display(true);}finally{busy=false;}
 }
 const b=document.createElement('button');b.className='button';b.textContent='فحص آخر تحديث';b.addEventListener('click',check);document.getElementById('printButton').before(b);
 try{const view=sessionStorage.getItem('ceo-view'),project=sessionStorage.getItem('ceo-project');if(view&&Object.hasOwn(views,view)){if(project&&(D.taskProjects||[]).some(p=>p.id===project))selectedProject=project;navigate(view);}}catch{}
 display();setInterval(check,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)check();});check();
})();
