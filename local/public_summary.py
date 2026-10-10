"""Public aggregate export for Drive/Slack sections; private detail stays local."""
import copy,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'local/private-dashboard-data.json'
def current():
    return json.loads((PRIVATE if PRIVATE.exists() else ROOT/'site/data.json').read_text(encoding='utf8'))
def counts(rows):
    allowed={'تم الإنجاز','قيد التنفيذ','بانتظار التنفيذ','لم تبدأ بعد','تم الحل','غير مسجلة','مفتوحة','مغلقة','مكتمل','Done','done','resolved','in progress','pending','not started'}
    states=collections.Counter((x.get('status') or 'غير مسجلة') if (x.get('status') or 'غير مسجلة') in allowed else 'حالة أخرى' for x in rows)
    return {'total':len(rows),'states':dict(states)}
def prepare(data):
    full=copy.deepcopy(data);full.pop('publicSummary',None)
    PRIVATE.write_text(json.dumps(full,ensure_ascii=False),encoding='utf8')
    encoded=json.dumps(full,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')
    (ROOT/'local/private-data.js').write_text('window.LOCAL_CEO_DATA = '+encoded+';',encoding='utf8')
    out=copy.deepcopy(full)
    summary={'checkedAt':full.get('fetchedAt'),'scope':'ملخصات وأرقام فقط لأقسام المهام والتوظيف والتحصيل والفرق وتقارير سلاك ودرايف. التفاصيل متاحة محليًا.','tasks':counts(full.get('tasks',[])),'archive':counts(full.get('archive',[])),'teams':{k:counts(v) for k,v in full.get('teams',{}).items()},'hiring':{'total':len(full.get('hiring',[])),'withRecommendation':sum(bool(x.get('recommendation')) for x in full.get('hiring',[]))},'collection':{'total':len(full.get('collection',[])),'withBalance':sum(isinstance(x.get('balance'),(int,float)) and x['balance']>0 for x in full.get('collection',[])),'duplicateRows':sum(bool(x.get('duplicate')) for x in full.get('collection',[]))},'orders':[{k:x.get(k) for k in ['date','total','riyadh','other']} for x in full.get('reports',{}).get('orders',[])],'callsReportCount':len(full.get('reports',{}).get('calls',[]))}
    for k in ['tasks','archive','hiring','collection','orderHistory','marketingCompleted','marketingCompletionPending','completedArchiveHistory']:out[k]=[]
    out['teams']={k:[] for k in full.get('teams',{})}
    out['reports']={'orders':[],'calls':[],'scope':'ملخصات عامة؛ تفاصيل التقارير محفوظة محليًا.'}
    out['whatsapp']={'reports':[],'archiveCount':0,'lastSuccessAt':full.get('whatsapp',{}).get('lastSuccessAt')}
    for k in ['marketingChannels','dailyCompletions','whatsappAssignmentReview']:out[k]={}
    out.pop('salesLegacy',None)
    out['dailyReport']={'date':full.get('dailyReport',{}).get('date'),'scheduleHour':18,'timezone':'Asia/Riyadh','sourceReviewComplete':False,'text':'تتوفر الأرقام المحدثة في أقسام الملخصات؛ تقرير الإدارة التفصيلي محفوظ محليًا.','preview':'ملخص عام دون تفاصيل داخلية.'}
    for s in out.get('sources',[]):
        if s.get('id')!='sales':
            s['url']='';s['details']='ملخصات عامة؛ تفاصيل المصدر محفوظة محليًا.'
            for k in ['channelId','channelUrl','syncError']:s.pop(k,None)
    if out.get('b2cExpenses'):
        out['b2cExpenses']['rows']=[{'date':x['date'],'spend':x['spend']} for x in out['b2cExpenses'].get('rows',[])]
    out['publicSummary']=summary
    return out

def recover(data):
    if 'publicSummary' not in data:return data
    full=current()
    protected={'publicSummary','sources','tasks','archive','hiring','collection','teams','reports','whatsapp','dailyReport','marketingChannels','dailyCompletions','orderHistory','marketingCompleted','marketingCompletionPending','completedArchiveHistory','whatsappAssignmentReview','salesLegacy'}
    full.update({k:v for k,v in data.items() if k not in protected})
    return full

