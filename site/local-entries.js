'use strict';
// User-authored records live outside synchronized snapshots.
(() => {
 const field=(key,label,type='text',required=false,options=[])=>({key,label,type,required,options});
 const title=field('title','العنوان','text',true), owner=field('owner','المسؤول'), note=field('note','ملاحظات','textarea'), url=field('url','رابط المصدر','url');
 const date=field('date','التاريخ','date',true), due=field('due','موعد التسليم / الاستحقاق','date');
 const status=field('status','الحالة','select',true,['لم تبدأ بعد','قيد التنفيذ','بانتظار الرد','تم الإنجاز']);
 const priority=field('priority','الأولوية','select',true,['عادي','مهم','عاجل','عاجل جدا']);
 const amount=(key,label)=>field(key,label+' (ريال)','number');
 const text=(key,label)=>field(key,label,'textarea');
 const choice=(key,label,options)=>field(key,label,'select',true,options);
 const schemas={
  overview:{name:'نقطة متابعة',fields:[title,owner,priority,status,due,text('description','التفاصيل'),note,url]},
  projects:{name:'مشروع',fields:[title,field('displayName','الاسم المختصر'),owner,field('company','الشركة'),field('phone','رقم التواصل','tel'),status,field('linkedTaskTitle','المهمة المرتبطة'),text('objective','هدف المشروع'),text('summary','الملخص'),text('outcome','آخر النتائج'),text('facts','بيانات المشروع'),text('decisions','قرارات تحتاج حسمًا'),text('updates','التحديثات'),text('nextSteps','الخطوات القادمة'),text('budgetPlan','خطة الميزانية'),field('location','رابط الموقع','url'),text('attachments','روابط المستندات والمرفقات'),text('documentsNote','ملاحظات المستندات'),url]},
  tasks:{name:'مهمة',fields:[title,owner,due,priority,status,note,url]},
  hiring:{name:'مرشح',fields:[field('name','اسم المرشح','text',true),field('position','المسمى الوظيفي','text',true),field('phone','الهاتف','tel'),field('email','البريد الإلكتروني','email'),field('experience','سنوات الخبرة','number'),field('interview','موعد المقابلة','datetime-local'),choice('recommendation','التوصية',['قيد المراجعة','يرشح للمقابلة','مقبول','غير مناسب']),amount('salary','الراتب المتوقع'),field('cv','رابط السيرة الذاتية','url'),note,url]},
  social:{name:'تقرير سوشيال ميديا',fields:[title,choice('platform','المنصة',['Instagram','TikTok','Snapchat','X','LinkedIn','Facebook','YouTube']),date,field('handle','اسم الحساب'),field('followers','المتابعون','number'),field('reach','الوصول','number'),field('impressions','المشاهدات','number'),field('likes','الإعجابات','number'),field('comments','التعليقات','number'),field('shares','المشاركات','number'),field('clicks','نقرات المتجر','number'),field('conversions','التحويلات','number'),amount('spend','الإنفاق'),text('content','المحتوى المنشور'),note,url]},
  b2c:{name:'سجل مبيعات B2C',fields:[title,date,field('order','رقم الطلب / التقرير'),field('customer','العميل'),field('orders','عدد الطلبات','number'),field('units','عدد الوحدات','number'),amount('gross','إجمالي المبيعات'),amount('discount','الخصومات'),amount('tax','الضريبة'),amount('shipping','الشحن'),amount('net','صافي المبيعات'),amount('refunds','المرتجعات'),amount('spend','الإنفاق'),choice('status','حالة الطلب',['جديد','قيد التجهيز','تم الشحن','مكتمل','ملغي','مرتجع']),note,url]},
  sales:{name:'فاتورة B2B',fields:[field('invoice','رقم الفاتورة','text',true),field('customer','العميل','text',true),owner,date,field('units','عدد الوحدات','number'),amount('gross','الإجمالي'),amount('net','الصافي'),amount('tax','الضريبة'),note,url]},
  collection:{name:'سجل تحصيل',fields:[field('customer','العميل','text',true),field('invoice','رقم الفاتورة','text',true),owner,field('city','المدينة'),date,due,amount('gross','قيمة الفاتورة'),amount('paid','المبلغ المحصل'),field('balance','الرصيد المتبقي (محسوب)','computed'),choice('status','الحالة',['لم يُحصّل','تحصيل جزئي','تم التحصيل','متأخر']),text('next','الإجراء القادم'),note,url]},
  teams:{name:'تكليف فريق',fields:[title,choice('team','الفريق',['الماركتنج','المحتوى والإبداع','خدمة العملاء']),owner,status,priority,field('start','تاريخ البداية','date'),field('end','تاريخ النهاية','date'),text('issue','المشكلة / العائق'),note,url]},
  reports:{name:'تقرير طلبات / مكالمات',fields:[title,choice('type','نوع التقرير',['طلبات','مكالمات']),date,field('author','معد التقرير'),field('total','إجمالي الطلبات / المكالمات','number'),field('riyadh','الرياض','number'),field('other','المناطق الأخرى','number'),field('answered','المكالمات المجابة','number'),field('missed','المكالمات الفائتة','number'),text('details','تفاصيل التقرير'),url,note]},
  whatsapp:{name:'تقرير واتساب',fields:[title,field('sender','المرسل','text',true),field('chat','المحادثة / المجموعة'),field('sentAt','وقت الرسالة','datetime-local',true),choice('direction','الاتجاه',['وارد','صادر']),choice('kind','نوع التقرير',['تقرير يومي','تكليف','إنجاز','متابعة']),field('text','نص التقرير','textarea',true),text('highlights','أبرز النقاط'),text('orders','تفاصيل الطلبات'),note,url]},
  linkedin:{name:'منشور لينكدإن',fields:[title,date,choice('status','حالة المنشور',['مسودة','للمراجعة','معتمد','منشور']),field('audience','الجمهور المستهدف'),field('text','نص المنشور','textarea',true),text('visualBrief','وصف التصميم'),text('editorNote','ملاحظات التحرير'),url]},
  daily:{name:'تقرير يومي',fields:[title,date,owner,text('tasks','المهام'),text('sales','المبيعات'),text('collection','التحصيل'),text('teams','متابعة الفرق'),text('achievements','الإنجازات'),text('blockers','المعوقات'),text('next','خطة الغد'),text('text','نص التقرير الكامل'),note]},
  archive:{name:'إنجاز',fields:[title,owner,field('department','القسم'),field('completionDate','تاريخ الإنجاز','date',true),due,priority,text('evidence','دليل الإنجاز'),note,url]},
  sources:{name:'مصدر متابعة',fields:[field('name','اسم المصدر','text',true),field('area','مجال المتابعة','text',true),choice('type','نوع المصدر',['Google Sheets','Google Drive','Slack','WhatsApp','موقع إلكتروني','ملف محلي','أخرى']),url,text('details','التفاصيل ونطاق المتابعة'),owner,note]}
 };
 let dbPromise,records=[],loadError=false,opener;
 function database(){
  if(!dbPromise)dbPromise=new Promise((resolve,reject)=>{
   const request=indexedDB.open('emiz-local-entries',1);
   request.onupgradeneeded=()=>request.result.createObjectStore('entries',{keyPath:'id'}).createIndex('view','view');
   request.onsuccess=()=>{const db=request.result;db.onversionchange=()=>db.close();resolve(db);};
   request.onerror=()=>reject(request.error);
   request.onblocked=()=>reject(new Error('database blocked'));
  }).catch(error=>{dbPromise=null;throw error;});
  return dbPromise;
 }
 async function transact(mode,action){const db=await database();return new Promise((resolve,reject)=>{const tx=db.transaction('entries',mode);let result;const req=action(tx.objectStore('entries'));req.onsuccess=()=>{result=req.result;};tx.oncomplete=()=>resolve(result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);});}
 const actions=document.createElement('div');actions.className='entry-actions';
 const add=document.createElement('button');add.className='button entry-primary';add.id='addEntryButton';add.type='button';
 const print=document.getElementById('printButton');print.before(actions);actions.append(add,print);
 const panel=document.createElement('section');panel.className='panel local-entries';panel.setAttribute('aria-label','الإضافات المحلية');content.before(panel);
 const toast=document.createElement('p');toast.className='entry-toast';toast.setAttribute('role','status');toast.setAttribute('aria-live','polite');panel.before(toast);
 const dialog=document.createElement('dialog');dialog.className='entry-dialog';dialog.setAttribute('aria-labelledby','entryDialogTitle');document.body.append(dialog);
 function paint(){
  const schema=schemas[state.view];add.textContent='+ إضافة '+schema.name;
  const rows=records.filter(r=>r.view===state.view).sort((a,b)=>b.createdAt.localeCompare(a.createdAt));
  panel.innerHTML=`<div class="panelhead"><div><h2>الإضافات المحلية <span class="tag">${rows.length}</span></h2><p>محفوظة في هذا المتصفح · مستقلة عن إحصاءات المصادر والمزامنة</p></div></div><div class="panelbody">${loadError?'<p role="alert">تعذرت قراءة قاعدة البيانات المحلية. تحقق من سماح المتصفح بالتخزين ثم أعد تحميل الصفحة.</p>':rows.length?`<div class="entry-grid">${rows.map(r=>`<article class="entry-card"><span class="tag green">محفوظ محليًا</span><h3>${E(r.values.title||r.values.name||r.values.customer||r.values.invoice)}</h3><small>${E(new Date(r.createdAt).toLocaleString('ar-SA'))}</small><details><summary>عرض جميع التفاصيل</summary><dl>${schema.fields.filter(f=>r.values[f.key]!==''&&r.values[f.key]!=null).map(f=>`<div><dt>${E(f.label)}</dt><dd>${f.type==='url'?link(r.values[f.key],r.values[f.key]):E(r.values[f.key])}</dd></div>`).join('')}</dl></details></article>`).join('')}</div>`:'<p class="entry-empty">ابدأ بإضافة '+E(schema.name)+'؛ ستظهر بياناته هنا بعد الحفظ.</p>'}</div>`;
 }
 function close(){if(dialog.querySelector('[type=submit]')?.disabled)return;dialog.close();opener?.focus();}
 function open(){
  opener=document.activeElement;const view=state.view,schema=schemas[view];
  dialog.innerHTML=`<form class="entry-form"><header><div><p class="eyebrow">${E(views[view][0])}</p><h2 id="entryDialogTitle">إضافة ${E(schema.name)}</h2><p>املأ البيانات أدناه. الحقول المميزة بـ * مطلوبة.</p></div><button type="button" class="entry-close" aria-label="إغلاق">×</button></header><div class="entry-fields">${schema.fields.map(f=>`<label class="${f.type==='textarea'?'entry-wide':''}" for="entry-${f.key}"><span>${E(f.label)}${f.required?' <b aria-hidden="true">*</b>':''}</span>${f.type==='textarea'?`<textarea id="entry-${f.key}" name="${f.key}" rows="3" maxlength="20000" ${f.required?'required':''}></textarea>`:f.type==='select'?`<select id="entry-${f.key}" name="${f.key}" required>${f.options.map(o=>`<option>${E(o)}</option>`).join('')}</select>`:`<input id="entry-${f.key}" name="${f.key}" type="${f.type==='computed'?'text':f.type}" ${f.required?'required':''} ${f.type==='number'?'min="0" step="any"':f.type==='computed'?'readonly':'maxlength="2000"'} ${['url','tel','email'].includes(f.type)?'dir="ltr"':''}>`}</label>`).join('')}</div><p class="entry-error" role="alert"></p><footer><span>حفظ محلي على هذا المتصفح والجهاز</span><div class="entry-actions"><button type="button" class="button entry-cancel">إلغاء</button><button type="submit" class="button entry-primary">حفظ ${E(schema.name)}</button></div></footer></form>`;
  const form=dialog.querySelector('form'),error=dialog.querySelector('.entry-error');
  dialog.querySelector('.entry-close').onclick=close;dialog.querySelector('.entry-cancel').onclick=close;
  form.oninput=()=>{error.textContent='';if(view==='collection'){const gross=Number(form.elements.gross.value),paid=Number(form.elements.paid.value);form.elements.balance.value=(gross-paid).toFixed(2);}};
  form.onsubmit=async event=>{
   event.preventDefault();const submit=form.querySelector('[type=submit]');if(submit.disabled)return;
   const values={};
   for(const f of schema.fields){const value=form.elements[f.key].value.trim();if(f.required&&!value){error.textContent='يرجى إكمال حقل '+f.label;form.elements[f.key].focus();return;}if(f.type==='url'&&value&&!/^https?:\/\//i.test(value)){error.textContent='استخدم رابطًا يبدأ بـ https:// أو http://';form.elements[f.key].focus();return;}values[f.key]=f.type==='number'&&value!==''?Number(value):value;if(f.type==='number'&&value!==''&&(!Number.isFinite(values[f.key])||values[f.key]<0)){error.textContent='أدخل قيمة رقمية صحيحة غير سالبة.';return;}}
   if(view==='collection'){if(values.paid>values.gross){error.textContent='المبلغ المحصل لا يمكن أن يتجاوز قيمة الفاتورة.';return;}values.balance=Math.round((Number(values.gross)-Number(values.paid))*100)/100;}
   if(view==='teams'&&values.start&&values.end&&values.end<values.start){error.textContent='تاريخ النهاية يجب أن يكون بعد تاريخ البداية أو مساويًا له.';return;}
   submit.disabled=true;submit.textContent='جارٍ الحفظ…';
   try{const record={id:crypto.randomUUID(),view,values,createdAt:new Date().toISOString()};await transact('readwrite',store=>store.add(record));records.push(record);loadError=false;submit.disabled=false;close();paint();toast.textContent='تم حفظ '+schema.name+' بنجاح في قاعدة البيانات المحلية.';}
   catch{error.textContent='تعذر الحفظ. تحقق من مساحة التخزين وسماح المتصفح بالتخزين المحلي ثم حاول مجددًا. بيانات النموذج ما زالت محفوظة هنا.';}
   finally{submit.disabled=false;submit.textContent='حفظ '+schema.name;}
  };
  dialog.showModal();dialog.querySelector('input,textarea,select')?.focus();
 }
 dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
 add.addEventListener('click',open);
 // The heading changes for every navigation, including links inside cards.
 new MutationObserver(()=>{toast.textContent='';paint();}).observe(document.getElementById('pageTitle'),{childList:true});
 async function reload(){try{records=await transact('readonly',store=>store.getAll());loadError=false;}catch{loadError=true;}paint();}
 window.addEventListener('focus',reload);paint();reload();
})();
