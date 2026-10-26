/* Presentation enhancements only. No source or task data is changed. */
(()=>{
 const sidebar=document.querySelector('.sidebar'),nav=sidebar?.querySelector('nav');
 if(!sidebar||!nav)return;
 const toggle=document.createElement('button');toggle.className='design-menu-toggle';toggle.type='button';toggle.textContent='الأقسام';toggle.setAttribute('aria-expanded','false');nav.id='dashboardNavigation';toggle.setAttribute('aria-controls',nav.id);sidebar.prepend(toggle);
 toggle.addEventListener('click',()=>{const open=sidebar.classList.toggle('menu-open');toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'إغلاق':'الأقسام'});
 const groups={overview:'الرئيسية',hiring:'الأفراد والمتابعة',social:'المبيعات والتسويق',collection:'التشغيل والفرق',meetings:'التقارير والسجلات'};
 for(const [view,label]of Object.entries(groups)){const item=nav.querySelector(`[data-view="${view}"]`);if(item){const heading=document.createElement('div');heading.className='design-section-title';heading.textContent=label;nav.insertBefore(heading,item)}}
 nav.addEventListener('click',e=>{if(!e.target.closest('[data-view]'))return;sidebar.classList.remove('menu-open');toggle.setAttribute('aria-expanded','false');toggle.textContent='الأقسام'});
 const hues=[260,210,160,25,330,185,45,285,140,355,225,75,305,195,15,245,110,315];
 nav.querySelectorAll('[data-view]').forEach((button,index)=>button.style.setProperty('--section-hue',hues[index%hues.length]));
 const content=document.getElementById('content');let queued=false;
 let taskLayout='cards';
 function enhance(){queued=false;for(const table of content.querySelectorAll('table')){if(table.classList.contains('shared-table')||table.closest('.design-table-scroll,.tablewrap,.table-wrap'))continue;const wrap=document.createElement('div');wrap.className='design-table-scroll';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','جدول البيانات — يمكن التمرير أفقيًا');table.before(wrap);wrap.append(table)}for(const b of nav.querySelectorAll('[data-view]')){if(b.classList.contains('active')){b.setAttribute('aria-current','page');document.body.dataset.section=b.dataset.view}else b.removeAttribute('aria-current')}
 const results=document.getElementById('sharedResults');if(results){results.dataset.layout=taskLayout;if(!document.getElementById('taskLayoutChoice')){const controls=document.createElement('div');controls.id='taskLayoutChoice';controls.className='layout-choice';controls.innerHTML='<span>طريقة العرض</span><button type="button" data-layout="cards">بطاقات</button><button type="button" data-layout="table">جدول</button>';results.before(controls);controls.addEventListener('click',e=>{const b=e.target.closest('[data-layout]');if(!b)return;taskLayout=b.dataset.layout;enhance()})}for(const b of document.querySelectorAll('#taskLayoutChoice button'))b.setAttribute('aria-pressed',String(b.dataset.layout===taskLayout));for(const note of results.querySelectorAll('.shared-note')){if(note.parentElement.tagName==='DETAILS')continue;const detail=document.createElement('details');detail.className='task-note-detail';const summary=document.createElement('summary');summary.textContent='التفاصيل وآخر تحديث';note.before(detail);detail.append(summary,note)}}
 }
 new MutationObserver(()=>{if(!queued){queued=true;requestAnimationFrame(enhance)}}).observe(content,{childList:true,subtree:true});enhance();
})();

