'use strict';
const syncDate=value=>value&&Number.isFinite(Date.parse(value))?new Intl.DateTimeFormat('ar-SA-u-ca-gregory-nu-latn',{dateStyle:'short',timeStyle:'short',timeZone:'Asia/Riyadh'}).format(new Date(value)):'غير متاح';
function showSyncStatus(connectionError=false){
  const sync=D.sync||{};
  const age=sync.checkedAt?(Date.now()-Date.parse(sync.checkedAt))/60000:Infinity;
  const fresh=age<Math.max(15,(sync.intervalMinutes||30)*2);
  const enabled=sync.enabled===true;
  const lastScheduled=D.automationHealth?.lastScheduledSuccessAt||D.automationHealth?.scheduledVerifiedAt;
  const verified=D.automationHealth?.status==='verified'&&lastScheduled&&(Date.now()-Date.parse(lastScheduled))/60000<Math.max(60,(sync.intervalMinutes||30)*2);
  const prefix=enabled?(verified?'مزامنة مجدولة كل '+(sync.intervalMinutes||30)+' دقيقة. ':'جدول التحديث كل '+(sync.intervalMinutes||30)+' دقيقة، لكن تشغيله التلقائي لم يُتحقق بعد. '):'المزامنة غير مفعّلة. ';
  document.getElementById('sidebarDate').textContent='آخر فحص: '+syncDate(sync.checkedAt||D.fetchedAt);
  document.querySelector('.sidebarfoot .scope').textContent=enabled?(verified?'التحديث التلقائي متحقق':'التحديث التلقائي يحتاج تحققًا'):'نسخة محلية';
  document.getElementById('freshness').classList.toggle('warning',!verified||connectionError||!fresh||!!sync.errors);
  document.querySelector('.sidebarfoot p').textContent='يلزم تشغيل الجهاز وCodex والاتصال بالإنترنت.';
  document.getElementById('freshness').textContent=prefix+'آخر فحص للمصادر: '+syncDate(sync.checkedAt||D.fetchedAt)+'. '+(connectionError?'تعذر الاتصال بالخدمة المحلية؛ البيانات المعروضة آخر نسخة محفوظة. ':!fresh?'لم تصل مزامنة حديثة؛ تحقق من تشغيل الجهاز وCodex. ':'')+(sync.errors?'تعذر تحديث '+N(sync.errors)+' من المصادر؛ احتُفظ ببياناتها السابقة. ':'')+'تاريخ تقرير المهام داخل المصدر: '+(D.taskReportDate||'غير مسجل')+'. تقارير المكالمات: الروابط فقط، دون أرقام المرفقات.';
  if(location.protocol==='file:')document.getElementById('freshness').textContent+=' هذه نسخة محفوظة؛ افتح Open-Dashboard.cmd للعرض الذي يتحدث تلقائيًا.';
}
async function refreshLocal(){
  if(location.protocol==='file:')return;
  try{
    const response=await fetch('/data.json?t='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(5000)});
    if(!response.ok)throw new Error('Local read failed');
    const next=await response.json();
    if(!validSnapshot(next))throw new Error('Invalid local snapshot');
    if(next.sync?.revision!==D.sync?.revision){
      const active=document.activeElement,focused=active?.id,selection=active?.selectionStart;
      const scroll=window.scrollY;
      const opened=[...document.querySelectorAll('details[open][data-detail-id]')].map(el=>el.dataset.detailId);
      Object.assign(D,next);
      urgentTasks.splice(0,urgentTasks.length,...D.tasks.filter(t=>urgent(t)&&t.status!=='تم الإنجاز').sort((a,b)=>Number(b.priority==='عاجل جدا')-Number(a.priority==='عاجل جدا')));
      shortlisted.splice(0,shortlisted.length,...D.hiring.filter(recommended));
      document.getElementById('navTasks').textContent=N(D.tasks.length);
      document.getElementById('currentDate').textContent=new Intl.DateTimeFormat('ar-SA-u-ca-gregory-nu-latn',{day:'numeric',month:'long',year:'numeric',timeZone:'Asia/Riyadh'}).format(new Date(D.snapshotDate+'T12:00:00Z'));
      render();
      document.querySelectorAll('details[data-detail-id]').forEach(el=>{el.open=opened.includes(el.dataset.detailId);});
      if(focused){const el=document.getElementById(focused);el?.focus({preventScroll:true});if(typeof selection==='number'&&el?.setSelectionRange)el.setSelectionRange(selection,selection);}
      window.scrollTo(0,scroll);
    }
    showSyncStatus();
  }catch{showSyncStatus(true);}
}
function validSnapshot(value){
  const tasks=rows=>Array.isArray(rows)&&rows.every(r=>r&&typeof r.title==='string'&&typeof r.owner==='string'&&typeof r.status==='string');
  return value&&tasks(value.tasks)&&tasks(value.archive)&&Array.isArray(value.hiring)&&Array.isArray(value.collection)
    &&tasks(value.teams?.marketing)&&tasks(value.teams?.creative)&&tasks(value.teams?.cx)
    &&Array.isArray(value.reports?.orders)&&Array.isArray(value.reports?.calls)
    &&Array.isArray(value.sources)&&['tasks','archive','hiring','sales','marketing','creative','cx','collection','orders','calls'].every(id=>value.sources.some(s=>s.id===id&&typeof s.url==='string'))
    &&typeof value.sync?.revision==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value.snapshotDate);
}
const originalRenderSources=renderSources;
renderSources=function(){
  originalRenderSources();
  document.querySelectorAll('.sourcecard').forEach((card,i)=>{
    const s=D.sources[i],p=document.createElement('p');
    p.className='scope-note';
    p.textContent=(s.syncStatus==='error'?'تعذر التحديث: '+s.syncError:s.syncStatus==='partial'?'تحديث ضمن النطاق الموضح':'تمت المزامنة')+' · آخر نجاح: '+syncDate(s.lastSuccessAt);
    card.appendChild(p);
  });
};
const syncButton=document.createElement('button');syncButton.className='button';syncButton.textContent='عرض آخر بيانات محفوظة';syncButton.title='يعرض آخر نسخة محلية؛ لا يبدأ سحب المصادر';syncButton.addEventListener('click',refreshLocal);document.getElementById('printButton').before(syncButton);
showSyncStatus();
if(location.protocol!=='file:'){setInterval(refreshLocal,15000);refreshLocal();}
