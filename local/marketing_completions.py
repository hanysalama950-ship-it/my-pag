"""User-authorized Ahmed Taher completion evidence, with reviewed task links."""
import json
import hashlib
import re
from pathlib import Path

AHMED='U0B3344PJ3W'
def norm(s): return re.sub(r'\s+',' ',str(s)).strip()

def enrich(data):
    path=Path(__file__).with_name('marketing-completions.json')
    spec=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'items':[]}
    messages={m['id']:m for c in data.get('marketingChannels',{}).values() for m in c.get('messages',[])}
    saved={r['id']:r for r in data.get('marketingCompleted',[])}
    for item in spec['items']:
        reply=messages.get(item['replyId'])
        parent=messages.get(item['taskMessageId'])
        identity='marketing-done-'+hashlib.sha256(item['canonicalKey'].encode()).hexdigest()[:20]
        if not reply or not parent: continue  # Preserve previously verified evidence beyond read window.
        if not (item.get('reviewed') and reply.get('userId')==AHMED and norm(item['evidence']) in norm(reply['body']) and 'تم' in item['evidence']):
            saved.pop(identity,None);continue
        saved[identity]=dict(id=identity,title=item['title'],owner='Ahmed Taher',department='التسويق',
            status='مكتملة بتأكيد أحمد طاهر',source='marketing-completion',priority='',
            due=reply['date'],reportDate=reply['date'],completedAt=reply['date'],
            completionDate=reply['date'],evidence=item['evidence'],url=reply['url'],
            taskUrl=parent['url'],taskMessageId=parent['id'],replyId=reply['id'],
            canonicalKey=item['canonicalKey'],note='تأكيد أحمد طاهر: '+item['evidence']+' · تاريخ الرد '+reply['date'])
    data['marketingCompleted']=sorted(saved.values(),key=lambda r:(r['completionDate'],r['id']),reverse=True)
    data['archive']=[r for r in data.get('archive',[]) if r.get('source')!='marketing-completion']+data['marketingCompleted']
    for m in messages.values():
        matches=[r for r in data['marketingCompleted'] if m['id'] in (r['taskMessageId'],r['replyId'])]
        m['completedTasks']=[{'title':r['title'],'date':r['completionDate'],'url':r['url']} for r in matches]
    linked={r['replyId'] for r in data['marketingCompleted']}
    data['marketingCompletionPending']=[m['id'] for m in messages.values() if m.get('userId')==AHMED and re.fullmatch(r'[*\s]*تم[*\s]*',m['body']) and m['id'] not in linked]
