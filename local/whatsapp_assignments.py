"""Locally archive reviewed WhatsApp assignments with paired completion evidence."""
import json
from pathlib import Path
from datetime import datetime

def enrich(data):
    path=Path(__file__).with_name('whatsapp-assignment-completions.json')
    if not path.exists(): return
    spec=json.loads(path.read_text(encoding='utf-8'))
    records=[]
    for item in spec['items']:
        if not item.get('reviewed'): continue
        assert item['request'] and item['evidence'] and item['owner']
        completed=datetime.fromisoformat(item['completedAt'])
        assert completed>=datetime.fromisoformat(item['assignedAt'])
        date=completed.date().isoformat()
        records.append(dict(id=item['id'],title=item['title'],owner=item['owner'],department=item['department'],status='مكتملة بدليل محادثة واتساب',source='whatsapp-assignment',due=date,completionDate=date,completedAt=item['completedAt'],priority='',dateBasis='تاريخ رسالة إثبات التنفيذ بتوقيت الرياض',evidence=item['evidence'],requestEvidence=item['request'],url='https://web.whatsapp.com/',note='تكليف أ. مهند: '+item['request']+' · دليل التنفيذ: '+item['evidence']+' · '+item['note']))
    data['archive']=[r for r in data['archive'] if r.get('source')!='whatsapp-assignment']+records
    data['whatsappAssignmentReview']={'count':len(records),'reviewedAt':spec['reviewedAt'],'scope':spec['scope'],'pending':spec.get('pending',[])}
