/* Presentation enhancements only. No source or task data is changed. */
(()=>{
 const sidebar=document.querySelector('.sidebar'),nav=sidebar?.querySelector('nav');
 if(!sidebar||!nav)return;
 const toggle=document.createElement('button');toggle.className='design-menu-toggle';toggle.type='button';toggle.textContent='الأقسام';toggle.setAttribute('aria-expanded','false');nav.id='dashboardNavigation';toggle.setAttribute('aria-controls',nav.id);sidebar.prepend(toggle);
 toggle.addEventListener('click',()=>{const open=sidebar.classList.toggle('menu-open');toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'إغلاق':'الأقسام'});
 const groups={overview:'الرئيسية',hiring:'الأفراد والمتابعة',social:'المبيعات والتسويق',collection:'التشغيل والفرق',meetings:'التقارير والسجلات'};
 for(const [view,label]of Object.entries(groups)){const item=nav.querySelector(`[data-view="${view}"]`);if(item){const heading=document.createElement('div');heading.className='design-section-title';heading.textContent=label;nav.insertBefore(heading,item)}}
 nav.addEventListener('click',e=>{if(!e.target.closest('[data-view]'))return;sidebar.classList.remove('menu-open');toggle.setAttribute('aria-expanded','false');toggle.textContent='الأقسام'});
 const content=document.getElementById('content');let queued=false;
 function enhance(){queued=false;for(const table of content.querySelectorAll('table')){if(table.classList.contains('shared-table')||table.closest('.design-table-scroll,.tablewrap,.table-wrap'))continue;const wrap=document.createElement('div');wrap.className='design-table-scroll';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','جدول البيانات — يمكن التمرير أفقيًا');table.before(wrap);wrap.append(table)}for(const b of nav.querySelectorAll('[data-view]')){if(b.classList.contains('active'))b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')}}
 new MutationObserver(()=>{if(!queued){queued=true;requestAnimationFrame(enhance)}}).observe(content,{childList:true,subtree:true});enhance();
})();
