"""Archive explicit completed source records without inventing completion dates."""
import hashlib
import re

DEPARTMENTS={'tasks':'المهام المباشرة','marketing':'التسويق','creative':'المحتوى','cx':'خدمة العملاء','collection':'التحصيل'}
DONE={'done','resolved','closed','completed','تم الإنجاز','مكتملة','تم الحل','تم التحصيل','محصل بالكامل'}
def norm(s):return re.sub(r'\s+',' ',str(s or '')).strip().lower()

def enrich(data):
    sources={s['id']:s for s in data.get('sources',[])}
    history={r['id']:r for r in data.get('completedArchiveHistory',[])}
    groups={'tasks':data.get('tasks',[]),'collection':data.get('collection',[]),**data.get('teams',{})}
    for key,rows in groups.items():
        if key not in DEPARTMENTS or sources.get(key,{}).get('syncStatus')=='error':continue
        for row in rows:
            identity='completed-'+hashlib.sha256((key+':'+str(row['id'])).encode()).hexdigest()[:24]
            if norm(row.get('rawStatus',row.get('status'))) not in DONE:
                history.pop(identity,None)  # Explicit reopening removes the current completion.
                continue
            title=row.get('title') or ('تحصيل فاتورة '+row.get('invoice','')+' — '+row.get('customer',''))
            completed=row.get('completedAt',row.get('completionDate',''))
            if key=='marketing':completed=completed or row.get('end','')
            history[identity]=dict(id=identity,title=title,owner=row.get('owner',''),department=DEPARTMENTS[key],
                status=row.get('status','مكتملة'),priority='',source='completed-section',sourceId=key,
                sourceRecordId=row['id'],completionDate=completed[:10],completedAt=completed,
                due=completed[:10],dateBasis='تاريخ الإنجاز الموثق' if completed else 'تاريخ الإنجاز غير مسجل في المصدر',
                note=(row.get('note','')+' · '+('تاريخ الإنجاز: '+completed[:10] if completed else 'الحالة مكتملة؛ تاريخ الإنجاز غير مسجل')).strip(' ·'),
                url=row.get('url') or sources.get(key,{}).get('url',''),evidence='حالة المصدر: '+row.get('status',''),
                archivedFromSnapshot=data.get('sync',{}).get('checkedAt'))
    base=[r for r in data.get('archive',[]) if r.get('source')!='completed-section']
    # Merge exact title + recorded owner matches; retain separate evidence links.
    def signature(r):return (norm(r.get('title')),norm(r.get('owner')).replace('هانى','هاني'))
    indexed={signature(r):r for r in base}
    for r in history.values():
        existing=indexed.get(signature(r))
        if existing:
            refs=existing.setdefault('completionSources',[])
            ref={'sourceId':r['sourceId'],'recordId':r['sourceRecordId'],'url':r['url']}
            if ref not in refs:refs.append(ref)
        else:base.append(r);indexed[signature(r)]=r
    data['completedArchiveHistory']=list(history.values())
    data['archive']=base
