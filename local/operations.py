"""Local warehouse evidence and complaint status; never writes to sources."""
from datetime import date, datetime

DEPARTMENT = 'قسم المستودع والتشغيل'
def valid(report):
    try:
        date.fromisoformat(report['date'])
        return all(type(report[k]) is int and report[k] >= 0 for k in ('total','riyadh','other')) and report['total']==report['riyadh']+report['other'] and report.get('url','').startswith('https://al-rossaisgroup.slack.com/')
    except (KeyError, ValueError, TypeError): return False

def title(r):
    return f"تم تجهيز وشحن {r['total']} طلبًا: {r['riyadh']} داخل الرياض و{r['other']} خارج الرياض."

def enrich(data):
    history={r['date']:r for r in data.get('orderHistory',[]) if valid(r)}
    history.update({r['date']:dict(r) for r in data.get('reports',{}).get('orders',[]) if valid(r)})
    data['orderHistory']=sorted(history.values(),key=lambda r:r['date'],reverse=True)
    archive=[r for r in data.get('archive',[]) if r.get('source')!='orders']
    for report in data['orderHistory']:
        match=None
        for wa in data.get('whatsapp',{}).get('reports',[]):
            if wa.get('messageDate')!=report['date'] or wa.get('orders')!={k:report[k] for k in ('total','riyadh','other')}: continue
            match=next((r for r in archive if r.get('sourceReportId')==wa.get('id') and 'شحن' in r.get('evidence','')),None)
            if match: break
        if match:
            match['department']=DEPARTMENT
            match['orderSourceUrl']=report['url']
            continue
        archive.append(dict(id='orders-'+report['date'],title=title(report),owner='',department=DEPARTMENT,
            due=report['date'],reportDate=report['date'],status='مكتملة حسب تقرير التجهيز',priority='',source='orders',
            evidence=title(report),note='تاريخ تقرير التجهيز: '+report['date'],url=report['url']))
    data['archive']=archive

def summary(data, now):
    lines=[]
    reports=[r for r in data.get('reports',{}).get('orders',[]) if valid(r) and r['date']<=now.date().isoformat()]
    if reports:
        r=max(reports,key=lambda r:r['date'])
        prefix='' if r['date']==now.date().isoformat() else 'آخر تقرير متاح ('+r['date']+'): '
        lines.append(prefix+title(r))
    else: lines.append('لم يتوفر تقرير موثق بعدد الطلبات حتى الآن.')
    source=next((s for s in data.get('sources',[]) if s['id']=='cx'),{})
    try: fresh=(now-datetime.fromisoformat(source['lastSuccessAt'].replace('Z','+00:00'))).total_seconds()<=3600
    except (KeyError,TypeError,ValueError): fresh=False
    rows=data.get('teams',{}).get('cx')
    if not fresh or source.get('syncStatus')!='ok' or not isinstance(rows,list):
        lines.append('تعذر التحقق من حالة شكاوى العملاء حاليًا.')
    elif any(not r.get('rawStatus','').strip() for r in rows):
        lines.append('توجد شكاوى عملاء تحتاج تأكيد حالتها.')
    elif any(r['rawStatus'].strip().lower() not in ('resolved','closed','done') for r in rows):
        lines.append('جارٍ العمل على حل شكاوى العملاء المفتوحة.')
    else: lines.append('شكاوى العملاء مستقرة.')
    return lines
