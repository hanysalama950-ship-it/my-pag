"""Validate reviewed daily actions against the current local source snapshot."""
import json
import re

def text(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()

def flatten(value):
    if isinstance(value,dict):return ' '.join(flatten(v) for v in value.values())
    if isinstance(value,list):return ' '.join(flatten(v) for v in value)
    return text(value)

def source_records(data):
    records={key:data.get(key,[]) for key in ['tasks','archive','hiring','collection']}
    records['archive']=[r for r in records['archive'] if r.get('source')!='whatsapp']
    records.update(data.get('teams',{}))
    records['sales']=data.get('sales',{}).get('invoices',[]) if data.get('sales') else []
    records.update(data.get('reports',{}))
    records['whatsapp']=data.get('whatsapp',{}).get('reports',[])
    for source in data.get('sources',[]):
        if source['id'].endswith('-channel'):
            channel=source['url'].rstrip('/').split('/')[-1]
            records[source['id']]=data.get('marketingChannels',{}).get(channel,{}).get('messages',[])
    return records

def validate(data,day):
    review=data.get('dailyCompletions',{})
    sources={s['id']:s for s in data.get('sources',[])}
    result={'complete':False,'items':[],'reviewedSourceIds':[],'issues':[]}
    if review.get('date')!=day or review.get('snapshotRevision')!=data.get('sync',{}).get('checkedAt'):
        result['issues'].append('مراجعة مصادر التقرير لم تكتمل للنسخة الحالية.')
        return result
    versions=review.get('sourceVersions',{})
    reviewed=set(review.get('reviewedSourceIds',[]))
    current={key for key,s in sources.items() if key in reviewed and s.get('lastSuccessAt') and versions.get(key)==s.get('lastSuccessAt') and s.get('syncStatus')!='error'}
    result['reviewedSourceIds']=sorted(current)
    records=source_records(data)
    seen=set()
    for item in review.get('items',[]):
        key=item.get('sourceId')
        target=next((r for r in records.get(key,[]) if str(r.get('id',r.get('row',r.get('invoice',r.get('date','')))))==str(item.get('sourceRecordId'))),None)
        blob=text(flatten(target)) if target else ''
        valid=(key in current and item.get('reviewed') is True and item.get('state')=='completed'
            and item.get('completionDate')==day and text(item.get('evidence'))
            and text(item['evidence']) in blob and text(item.get('dateEvidence'))
            and day in text(item['dateEvidence']) and text(item['dateEvidence']) in blob
            and text(item.get('department')) and text(item.get('title')))
        if valid and key=='marketing':
            valid=target.get('rawStatus','').lower()=='done' and target.get('end')==day
        if valid and key in ['tasks','archive','hiring','creative','cx','collection']:
            # Due/start/end/complaint dates do not become completion dates.
            valid=(target.get('completedAt','')[:10]==day or target.get('completionDate')==day
                or (text(item['dateEvidence']) in text(target.get('note')) and day in text(target.get('note'))))
        if not valid:
            result['issues'].append('بند مستبعد لعدم تطابق الدليل أو تاريخ المصدر: '+text(item.get('title')))
            continue
        signature=text(item.get('canonicalKey')) or (text(item['department'])+'|'+text(item['title']))
        if signature not in seen:
            result['items'].append(item);seen.add(signature)
    if current!=set(sources):result['issues'].append('مصادر لم تكتمل مراجعتها: '+'، '.join(sorted(set(sources)-current)))
    result['complete']=current==set(sources) and not result['issues']
    return result
