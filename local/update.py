"""Build the local dashboard from read-only connector responses."""
import argparse, collections, csv, hashlib, io, json, re, os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
OWNERS = {'U0B45CU4HR6':'moutaz.nasser','U0B4BFMBSSU':'Hisham Helal','U0BGH1TD1MW':'mohamed.alsayed','U0B3BD1H4Q3':'AMR ELSHORAKY','U0B7Z23F3N2':'mohammed alsayed','U0B3LGXS70T':'ahmed.fetouhe','U0BNZFLJMFG':'Raghad mohammed yanbuawi','U0BAR93RB7E':'Jihen Remili','U0BARNC0FD2':'aya wael','U0BBK7630EN':'fawzia.samir','U0B3344PJ3W':'Ahmed Taher','U0B33AT4NVA':'Mohamed Helaley','U0B341VE18F':'mihaf'}
STATUS = {'done':'تم الإنجاز','in progress':'قيد التنفيذ','pending':'بانتظار التنفيذ','not started':'لم تبدأ بعد','resolved':'تم الحل'}
def clean(v): return str(v if v is not None else '').strip()
def owner(v): return re.sub(r'<@(U\w+)(?:\|([^>]+))?>', lambda m: OWNERS.get(m[1], m[2] or m[1]), clean(v))
def value(row, i): return clean(row[i]) if i < len(row) else ''
def number(v):
    if not clean(v): return None
    n=Decimal(clean(v).replace(',', ''))
    if not n.is_finite(): raise ValueError('قيمة رقمية غير صالحة في المصدر')
    return float(n)
def atomic(path, text):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(text, encoding='utf-8')
    os.replace(temp, path)
def rows(inp):
    if 'values' not in inp: raise ValueError('لم تصل صفوف المصدر')
    return inp['values']
def tasks(inp, url, archive=False):
    data = rows(inp)
    start = next((i for i,r in enumerate(data) if value(r,0)=='المهمة' and 'موعد' in value(r,2)), None)
    if start is None: raise ValueError('تغيرت عناوين أعمدة المهام')
    result, excluded = [], 0
    for i,r in enumerate(data[start+1:], start+2):
        if not value(r,0):
            excluded += bool(value(r,3)) if archive else 0
            continue
        result.append(dict(id=('archive-' if archive else 'task-')+str(i),row=i,title=value(r,0),owner=value(r,1),due=value(r,2),priority='' if archive else value(r,3),status=value(r,3 if archive else 4),note=value(r,4 if archive else 5),url=url+'&range=A'+str(i)+':'+('E' if archive else 'F')+str(i)))
    return result, excluded, value(data[0],0)
def listrows(inp, required):
    pages=inp.get('pages',[])
    if not pages or pages[-1].get('next_cursor'): raise ValueError('لم تكتمل صفحات القائمة')
    output=[]
    seen=set()
    for page in pages:
        text=page.get('result','')
        text=re.sub(r'\n# More records available\.[\s\S]*$', '', text)
        reader=csv.DictReader(io.StringIO(text))
        if not set(required).issubset(reader.fieldnames or []): raise ValueError('تغيرت أعمدة قائمة Slack')
        for r in reader:
            rid=r.get('Record ID','')
            if not rid or rid in seen: continue
            seen.add(rid)
            output.append({k:clean(v) for k,v in r.items() if k is not None})
    return output
def team(inp, key):
    title='ORDER' if key=='cx' else 'Task'
    status='status' if key=='marketing' else 'STATUS'
    who={'marketing':'owner','creative':'person Responsible','cx':'OWNER'}[key]
    output=[]
    for r in listrows(inp, ['Record ID',title,status,who]):
        if not r[title]: continue
        s=r[status]
        output.append(dict(id=r['Record ID'],title=('طلب ' if key=='cx' else '')+r[title],owner=owner(r[who]),status=STATUS.get(s.lower(),s or 'غير مسجلة'),rawStatus=s,start=r.get({'marketing':'Start Date','creative':'start Date','cx':'DATE'}[key],''),end=r.get('completion date' if key=='marketing' else 'End Date',''),note=r.get('comment' if key=='marketing' else 'COMMENTS' if key=='creative' else 'Respond','') or r.get('ACTION TAKEN',''),issue=r.get('ISSUE TYPE','')))
    return output
def collection(inp):
    output=[]
    for r in listrows(inp,['Record ID','اسم العميل','رقم الفاتورة','الرصيد','تاريخ الاستحقاق']):
        if not r['اسم العميل']: continue
        output.append(dict(id=r['Record ID'],customer=r['اسم العميل'],invoice=r['رقم الفاتورة'],gross=number(r.get('قيمة الفاتورة الاجمالية')),paid=number(r.get('المدفوع')),balance=number(r['الرصيد']),due=r['تاريخ الاستحقاق'],date=r.get('تاريخ الفاتورة',''),status=r.get('الحالة',''),owner=owner(r.get('المندوب المسؤل')),city=r.get('المدينة',''),note=r.get('اخر تواصل',''),next=r.get('الاجراء التالي','')))
    counts=collections.Counter(re.sub(r'\s','',r['invoice']) for r in output if r['invoice'])
    for r in output: r['duplicate']=bool(r['invoice'] and counts[re.sub(r'\s','',r['invoice'])]>1)
    return output
def reports(inp, kind):
    text=inp.get('messages')
    if text is None or not text.startswith('Channel:'): raise ValueError('لم تصل رسائل القناة')
    out=[]
    for block in re.split(r'(?==== Message from )', text)[1:]:
        m=re.search(r'=== Message from (.*?) <.*?> \(.*?\) at (\d{4}-\d{2}-\d{2}).*?===\s*\nMessage TS: (\d+\.\d+)\n([\s\S]*)', block)
        if not m: continue
        author,date,ts,body=m.groups()
        url='https://al-rossaisgroup.slack.com/archives/'+('C0B04N23NAX' if kind=='orders' else 'C0C06E5AZ32')+'/p'+ts.replace('.','')
        if kind=='calls':
            if 'Files:' not in body: continue
            title=body.split('Files:')[0].strip() or body.split('Files:',1)[1].split(' (ID:')[0].strip()
            out.append(dict(date=date,title=title,author=author,url=url))
        else:
            plain=body.replace('*','').translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789'))
            if not ('تجهيز' in plain and 'شحن' in plain): continue
            d=re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',plain)
            total=re.search(r'شحن\s*\(\s*(\d+)',plain)
            inside=re.search(r'داخل الرياض\s*\(\s*(\d+)',plain)
            outside=re.search(r'خارج الرياض\s*\(\s*(\d+)',plain)
            if not all([d,total,inside,outside]): raise ValueError('تقرير طلبات جديد يحتاج مراجعة تنسيق الأرقام')
            if int(total[1])!=int(inside[1])+int(outside[1]): raise ValueError('إجمالي تقرير الطلبات لا يطابق التفصيل')
            report_date=datetime(int(d[3]),int(d[2]),int(d[1])).date().isoformat()
            if not any(r['date']==report_date for r in out): out.append(dict(date=report_date,total=int(total[1]),riyadh=int(inside[1]),other=int(outside[1]),url=url))
    return out
def sales(inp, today):
    period=today[:7]
    tables=[]
    for part in inp['content'].split('\f'):
        reader=csv.DictReader(io.StringIO(part))
        tables.append([{clean(k):clean(v) for k,v in r.items() if k is not None} for r in reader])
    invoice_tables=[t for t in tables if t and 'قيمة الفاتورة الاجمالية' in t[0] and any(k.startswith(period+'-01') for k in t[0])]
    period_note=''
    if not invoice_tables:
        available=sorted({k[:7] for t in tables if t and 'قيمة الفاتورة الاجمالية' in t[0] for k in t[0] if re.match(r'^\d{4}-\d{2}-01(?: |$)',k) and k[:7]<period})
        if available:
            requested=period; period=available[-1]
            invoice_tables=[t for t in tables if t and 'قيمة الفاتورة الاجمالية' in t[0] and any(k.startswith(period+'-01') for k in t[0])]
            period_note=' لا يوجد جدول واضح للشهر '+requested+'؛ المعروض أحدث فترة متاحة: '+period+'.'
    if len(invoice_tables)!=1: raise ValueError('جدول مبيعات الشهر الحالي غير محدد؛ احتُفظ بالملخص السابق')
    datekey=next(k for k in invoice_tables[0][0] if k.startswith(period+'-01'))
    invoices=[]; issues=[]
    for r in invoice_tables[0]:
        date=r[datekey][:10]
        if not r.get('اسم العميل') or not r.get('رقم الفاتورة') or date[:7]!=period or not period+'-01'<=date<=today: continue
        fields=['قيمة الفاتورة غير شامل الضريبه','قيمة ضريبة القيمة المضافة','قيمة الفاتورة الاجمالية']
        if any(not r.get(k) for k in fields): raise ValueError('فاتورة بمبلغ ناقص؛ تحتاج مراجعة المصدر')
        net,tax,gross=[Decimal(str(number(r[k]))) for k in fields]
        invoices.append(dict(invoice=r['رقم الفاتورة'],customer=r['اسم العميل'],owner=r.get('المندوب',''),date=date,units=int(Decimal(r.get('عدد العبوات') or '0')),gross=float(gross),net=float(net),tax=float(tax)))
        if abs(net+tax-gross)>Decimal('.02'): issues.append(r['رقم الفاتورة'])
    c_tables=[t for t in tables if t and 'تاريخ التحصيل' in t[0] and 'المبلغ المحصل' in t[0]]
    if not c_tables: raise ValueError('لم يظهر جدول التحصيل في القراءة النصية')
    collections_rows=[r for t in c_tables for r in t if r.get('اسم العميل') and r['تاريخ التحصيل'][:7]==period and period+'-01'<=r['تاريخ التحصيل'][:10]<=today]
    collection_values=[]; invalid_collections=[]
    for r in collections_rows:
        try:
            amount=number(r['المبلغ المحصل'])
            if amount is None: raise ValueError('مبلغ فارغ')
            collection_values.append(Decimal(str(amount)))
        except (ValueError,ArithmeticError):
            invalid_collections.append({'customer':r['اسم العميل'],'date':r['تاريخ التحصيل'],'value':r['المبلغ المحصل']})
    notes=['سجل التحصيل منفصل عن الفواتير؛ تأكيد الرصيد يحتاج مطابقة كل تحصيل بفاتورته.','لم يُحسب تحقيق الهدف لعدم التحقق من اكتمال بيانات الأهداف ومطابقتها بالمندوبين.']
    if invalid_collections:
        notes.insert(0,'إجمالي التحصيل غير مكتمل؛ المجموع المعروض يشمل المبالغ الرقمية فقط. تحتاج مراجعة: '+ '؛ '.join(r['customer']+' — '+r['date'][:10]+' — القيمة: '+r['value'] for r in invalid_collections))
    if issues: notes.insert(0,'فروق بين الإجمالي المسجل وصافي الفاتورة مع الضريبة في: '+ '، '.join(issues)+'. أُبقيت القيم الأصلية.')
    return dict(period=period,modifiedTime=inp.get('modifiedTime'),scope='ملخص '+period+' من القراءة النصية المتاحة لملف Excel؛ اكتمال الملف كله غير متحقق.'+period_note,invoices=invoices,gross=float(sum((Decimal(str(r['gross'])) for r in invoices),Decimal(0))),units=sum(r['units'] for r in invoices),collectionsTotal=float(sum(collection_values,Decimal(0))),collectionCount=len(collections_rows),invalidCollections=invalid_collections,collectionsComplete=not invalid_collections,notes=notes)
def export(data):
    expense_path=ROOT/'local/b2c-expenses.json'
    if expense_path.exists(): data['b2cExpenses']=json.loads(expense_path.read_text(encoding='utf-8'))
    social_path=ROOT/'local/social-data.json'
    if social_path.exists(): data['social']=json.loads(social_path.read_text(encoding='utf-8'))
    b2c_path=ROOT/'local/b2c-data.json'
    if b2c_path.exists(): data['b2c']=json.loads(b2c_path.read_text(encoding='utf-8'))
    projects_dir=ROOT/'task-projects'
    if projects_dir.exists():
        data['taskProjects']=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(projects_dir.glob('*/project.json'))]
    repair_path = ROOT/'local/repair-state.json'
    try:
        repair = json.loads(repair_path.read_text(encoding='utf-8'))
        state_path=ROOT/'local/sync-state.json'
        state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
        data['automationHealth'] = {'status':repair.get('status','unknown'),
            'scheduledVerifiedAt':repair.get('scheduledVerifiedAt'),
            'lastScheduledSuccessAt':state.get('lastScheduledSuccessAt'),
            'message':'التشغيل التلقائي لم يُتحقق؛ آخر دورة مجدولة تعذرت بسبب بيئة تشغيل Codex.' if repair.get('status')!='verified' else 'تم التحقق من دورة تلقائية ناجحة.'}
    except (OSError,ValueError):
        data['automationHealth'] = {'status':'unknown','scheduledVerifiedAt':None,'message':'حالة التحديث التلقائي غير متاحة.'}
    linkedin_path = ROOT/'local/linkedin-content.json'
    if linkedin_path.exists():
        data['linkedin'] = json.loads(linkedin_path.read_text(encoding='utf-8'))
    from archive_enrichment import enrich
    enrich(data)
    from operations import enrich as enrich_operations
    enrich_operations(data)
    from marketing_completions import enrich as enrich_marketing
    enrich_marketing(data)
    from completed_archive import enrich as enrich_completed
    from whatsapp_assignments import enrich as enrich_assignments
    enrich_assignments(data)
    enrich_completed(data)
    # User assignment applies only to archive rows without a recorded owner.
    for task in data.get('archive', []):
        if str(task.get('owner') or '').strip() in ['', 'غير مسجل', 'غير محدد', 'غير مسجلة']:
            task['owner'] = 'هاني'
            task['ownerAssignment'] = 'تعيين المستخدم في الأرشيف المحلي'
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    atomic(SITE/'data.js','window.CEO_DATA = '+encoded+';\n')
    atomic(SITE/'data.json',json.dumps(data,ensure_ascii=False))
    atomic(ROOT/'sources.json',json.dumps(data['sources'],ensure_ascii=False,indent=2))
    html=(SITE/'index.html').read_text(encoding='utf-8')
    html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(SITE/'style.css').read_text(encoding='utf-8')+'</style>')
    names=['data.js','slack-ui.js','app.js','local-sync.js','local-entries.js']
    for name in names: html=html.replace('<script src="'+name+'" defer></script>','')
    code='\n'.join((SITE/name).read_text(encoding='utf-8') for name in names if (SITE/name).exists()).replace('</script','<\\/script')
    html=html.replace('</body>','<script>document.addEventListener("DOMContentLoaded",()=>{'+code+'\n});</script></body>')
    atomic(ROOT/'dashboard.html',html)
def run(inbox, current):
    checked=inbox['checkedAt']
    now=datetime.fromisoformat(checked.replace('Z','+00:00'))
    today=now.astimezone(timezone(timedelta(hours=3))).date().isoformat()
    oldtime=current.get('fetchedAt')
    inputs=inbox.get('inputs',{})
    for s in current['sources']:
        # WhatsApp is read through the linked browser, independently of connectors.
        if s['id'] in ['whatsapp','marketing-channel','creative-channel','team-marketing-channel']: continue
        key=s['id']; s.setdefault('lastSuccessAt',oldtime); s['lastCheckedAt']=checked
        try:
            if key=='hiring':
                names=rows(inputs['hiringNames']); recs=rows(inputs['hiringRecommendations'])
                if value(names[0],0)!='الاسم' or value(recs[0],0)!='التوصية النهائية': raise ValueError('تغيرت عناوين التوظيف')
                current['hiring']=[dict(row=i+1,name=value(r,0),recommendation=value(recs[i],0) if i<len(recs) else '',url=s['url']+'&range=A'+str(i+1)+':V'+str(i+1)) for i,r in enumerate(names) if i>0 and value(r,0)]
            elif key in ['tasks','archive']:
                current[key],excluded,reportdate=tasks(inputs[key],s['url'],key=='archive')
                if key=='tasks': current['taskReportDate']=reportdate; s['sourceDate']=reportdate
                else: current['archiveExcluded']=excluded
            elif key in ['marketing','creative','cx']: current['teams'][key]=team(inputs[key],key)
            elif key=='collection': current[key]=collection(inputs[key])
            elif key=='sales': current[key]=sales(inputs[key],today)
            elif key in ['orders','calls']: current['reports'][key]=reports(inputs[key],key)
            s['syncStatus']='partial' if key in ['sales','calls'] else 'ok'
            s['lastSuccessAt']=checked; s.pop('syncError',None); s['status']='read'
            s['details']={'tasks':'قراءة تبويب المتابعة؛ تاريخ التقرير داخل المصدر: '+current['taskReportDate'],'archive':'سجلات المهام المسماة؛ التكرارات محفوظة كما في المصدر.','hiring':'أسماء المرشحين والتوصية النهائية في تبويب رئيس الحسابات.','sales':current.get('sales',{}).get('scope','قراءة نصية محدودة.'),'collection':'قراءة القائمة كاملة؛ الأرصدة المعروضة تحتاج مطابقة الفواتير.','marketing':'قراءة قائمة الماركتنج كاملة.','creative':'قراءة قائمة المحتوى كاملة.','cx':'قراءة قائمة شكاوى العملاء كاملة.','orders':'آخر 10 رسائل بالقناة؛ استخراج تقارير الطلبات ذات الأرقام الصريحة.','calls':'روابط التقارير في آخر 10 رسائل. أعداد المكالمات داخل المرفقات غير متحققة.'}[key]
        except (ValueError,KeyError,TypeError,IndexError,ArithmeticError) as exc:
            s['syncStatus']='error'; s['syncError']=str(exc) if not isinstance(exc,KeyError) else 'تعذرت قراءة المصدر في هذه الدورة'
    from marketing_channels import update as update_marketing_channels
    update_marketing_channels(inbox,current)
    current['snapshotDate']=today; current['fetchedAt']=checked
    current['sync']={**current.get('sync',{}),'checkedAt':checked,'intervalMinutes':30,'revision':checked,'engine':'Codex local heartbeat','errors':sum(s['syncStatus']=='error' for s in current['sources'])}
    current['reports']['scope']='آخر 10 رسائل في كل قناة. أرقام المكالمات داخل المرفقات غير متحققة؛ يقتصر التحديث على روابط تقاريرها.'
    return current
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('inbox'); p.add_argument('--consume',action='store_true'); args=p.parse_args()
    path=Path(args.inbox).resolve()
    data=json.loads((SITE/'data.js').read_text(encoding='utf-8').strip()[len('window.CEO_DATA = '):-1])
    updated=run(json.loads(path.read_text(encoding='utf-8-sig')),data)
    export(updated)
    if args.consume and path.parent.name=='work' and path.name.startswith('sync-inbox-'): path.unlink()
    print(json.dumps({'checkedAt':updated['sync']['checkedAt'],'errors':updated['sync']['errors'],'tasks':len(updated['tasks']),'taskReportDate':updated['taskReportDate'],'sources':[{k:s.get(k) for k in ['id','syncStatus','syncError']} for s in updated['sources']]},ensure_ascii=False))
