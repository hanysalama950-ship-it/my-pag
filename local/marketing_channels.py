"""Read-only Slack channel updates, alongside the two complete task lists."""
import re

CHANNELS = {'marketing-channel':('C0C1KG3UE3B','marketing-master-task-list'),
            'creative-channel':('C0C0G8QGBSS','creative-team'),
            'team-marketing-channel':('C0B0901QXSA','team-marketing')}

def parse(value, channel):
    text = value.get('messages','')
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m:chr(int(m[1],16)), text)
    if not text.startswith('Channel:') or channel not in text.splitlines()[0]:
        raise ValueError('لم تصل بيانات قناة الماركتنج المحددة')
    rows = []
    for block in re.split(r'(?==== Message from )',text)[1:]:
        m = re.search(r'=== Message from (.*?) <.*?> \((U[A-Z0-9]+)\) at (\d{4}-\d{2}-\d{2}) ([^\n]*?) ===\s*\nMessage TS: (\d+\.\d+)\n([\s\S]*)',block)
        if not m: raise ValueError('تغير تنسيق رسائل قناة الماركتنج')
        author,user_id,date,time,ts,body=m.groups()
        body=body.strip()
        if 'has joined the channel' in body or not re.search(r'[\w\u0600-\u06ff]',body): continue
        rows.append(dict(id=channel+':'+ts,channelId=channel,author=author,userId=user_id,date=date,
            body=body,url='https://al-rossaisgroup.slack.com/archives/'+channel+'/p'+ts.replace('.','')))
    return dict(messages=rows,coverage='القناة كاملة وقت القراءة' if 'no more messages' in value.get('pagination_info','').lower() else 'آخر 100 رسالة؛ المهام في القائمتين تقرأ كاملة')

def update(inbox,data):
    records=data.setdefault('marketingChannels',{})
    for key,(channel,name) in CHANNELS.items():
        source=next((s for s in data['sources'] if s['id']==key),None)
        if source is None:
            source=dict(id=key,area='تقارير الماركتنج',name=name,type='Slack channel',
                url='https://al-rossaisgroup.slack.com/archives/'+channel)
            data['sources'].append(source)
        source['lastCheckedAt']=inbox['checkedAt']
        try:
            parsed=parse(inbox.get('inputs',{})[key],channel)
            records[channel]={**parsed,'name':name,'lastSuccessAt':inbox['checkedAt']}
            source.update(status='read',syncStatus='ok',lastSuccessAt=inbox['checkedAt'],
                details=parsed['coverage']+'؛ الرسائل سياق متابعة ولا تضاف تلقائيًا إلى عدد مهام القوائم.')
            source.pop('syncError',None)
        except (KeyError,ValueError,TypeError) as error:
            source.update(syncStatus='error',syncError=inbox.get('errors',{}).get(key,str(error)))
