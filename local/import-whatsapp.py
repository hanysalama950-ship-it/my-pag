"""Merge reports read from the authorized WhatsApp Web conversation. Never logs in."""
import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from update import SITE, export

CHAT = 'أ مهند الرصيص ١'
DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

def normalize(item):
    if item.get('direction') != 'outgoing':
        raise ValueError('Only the user’s sent reports are in scope')
    text = item['text'].strip()
    stamp = item['sourceTimestamp']
    m = re.match(r'^\[(\d{1,2}:\d{2} [AP]M), (\d{1,2}/\d{1,2}/\d{4})\]', stamp)
    if not m:
        raise ValueError('Message timestamp format requires review')
    sent = datetime.strptime(m[2]+' '+m[1], '%m/%d/%Y %I:%M %p').isoformat()
    if len(text) < 80 or not any(word in text for word in ['تم ', 'متابعة', 'تقرير', 'بخصوص']):
        raise ValueError('Message is not a verified text report')
    highlights = item.get('highlights', [])
    for h in highlights:
        if not h.get('text') or h['text'] not in text:
            raise ValueError('A highlight must quote the source text exactly')
    normalized = text.translate(DIGITS)
    orders = re.search(r'شحن\s*(\d+)\s*طلبية\s*[:：]\s*(\d+)\s*داخل الرياض\s*و\s*(\d+)\s*خارج الرياض', normalized)
    metrics = None
    if orders:
        total, inside, outside = map(int, orders.groups())
        if total == inside + outside:
            metrics = {'total':total, 'riyadh':inside, 'other':outside}
    identity = hashlib.sha256((CHAT+'\n'+sent+'\n'+text).encode()).hexdigest()[:24]
    return {'id':'wa-'+identity, 'sentAtLocal':sent, 'messageDate':sent[:10],
            'dateBasis':'تاريخ إرسال الرسالة؛ لم يُحدد تاريخ مستقل للتقرير',
            'direction':'outgoing', 'text':text, 'highlights':highlights,
            'validationWarnings':(['الإجمالي لا يساوي مجموع داخل الرياض وخارجها؛ لم تُعتمد أرقام الطلبات.'] if orders and metrics is None else []),
            'orders':metrics, 'kind':item.get('kind','متابعة يومية')}

def merge(current, payload, checked, scheduled=False):
    if payload.get('chatName') != CHAT:
        raise ValueError('Conversation is outside the authorized scope')
    if scheduled and payload.get('readingVerified') is not True:
        raise ValueError('A scheduled check must confirm a fresh browser read')
    incoming = [normalize(x) for x in payload['reports']]
    result = copy.deepcopy(current)
    previous = result.get('whatsapp', {})
    records = {r['id']:r for r in previous.get('reports', [])}
    for record in incoming:
        # Whitespace-only rendering differences must not create another report.
        signature = (record['sentAtLocal'], re.sub(r'\s+', ' ', record['text']).strip())
        for prior in records.values():
            if (prior['sentAtLocal'], re.sub(r'\s+', ' ', prior['text']).strip()) == signature:
                record['id'] = prior['id']
                break
        old = records.get(record['id'])
        if old and old.get('highlights') and not record['highlights']:
            record['highlights'] = old['highlights']
        records[record['id']] = record
    if not records:
        raise ValueError('No verified reports; prior data must be retained')
    result['whatsapp'] = {**previous, 'chatName':CHAT,
        'reports':sorted(records.values(),key=lambda r:(r['sentAtLocal'],r['id']),reverse=True),
        'lastSuccessAt':checked, 'historyComplete':False,
        'historyNote':payload.get('historyNote','قراءة محدودة للرسائل الظاهرة في المتصفح؛ ليست أرشيفًا كاملًا.'),
        'automaticSyncVerified':scheduled or previous.get('automaticSyncVerified',False),
        'collectionMethod':'WhatsApp Web · قراءة مباشرة من واجهة المحادثة'}
    result['whatsapp'].pop('lastError',None)
    if scheduled: result['whatsapp']['scheduledVerifiedAt']=checked
    src = next((s for s in result['sources'] if s['id']=='whatsapp'), None)
    if src is None:
        src = {'id':'whatsapp'}
        result['sources'].append(src)
    src.update({'area':'التقارير المرسلة للرئيس التنفيذي','name':CHAT,
        'type':'WhatsApp Business','url':'https://web.whatsapp.com/',
        'status':'read','syncStatus':'partial','lastSuccessAt':checked,'lastCheckedAt':checked,
        'details':'تقارير نصية من المحادثة الخاصة؛ السجل غير مكتمل. التحديث التلقائي من واتساب لم يُتحقق بعد.'})
    if result['whatsapp']['automaticSyncVerified']:
        src['details']='تقارير نصية من المحادثة الخاصة؛ السجل غير مكتمل. نجحت قراءة مجدولة عبر المتصفح؛ يلزم استمرار جلسة واتساب.'
    src.pop('syncError',None)
    # A WhatsApp import does not pretend Google/Slack were refreshed.
    result['sync'] = {**result.get('sync',{}),'revision':checked,
        'errors':sum(s.get('syncStatus')=='error' for s in result['sources'])}
    return result

def mark_error(current, message, checked):
    result=copy.deepcopy(current)
    source=next(s for s in result['sources'] if s['id']=='whatsapp')
    source.update({'syncStatus':'error','syncError':message,'lastCheckedAt':checked})
    result['whatsapp']['lastError']=message
    result['sync']={**result['sync'],'revision':checked,
        'errors':sum(s.get('syncStatus')=='error' for s in result['sources'])}
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('inbox',nargs='?')
    parser.add_argument('--scheduled',action='store_true')
    parser.add_argument('--error')
    args=parser.parse_args()
    current=json.loads((SITE/'data.json').read_text(encoding='utf-8'))
    checked=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    if args.error:
        updated=mark_error(current,args.error,checked)
    else:
        if not args.inbox: parser.error('inbox or --error is required')
        payload=json.loads(Path(args.inbox).read_text(encoding='utf-8-sig'))
        updated=merge(current,payload,checked,scheduled=args.scheduled)
    export(updated)
    print(json.dumps({'whatsappReports':len(updated['whatsapp']['reports']),
        'lastCheckedAt':checked,'lastSuccessAt':updated['whatsapp']['lastSuccessAt'],
        'syncError':updated['whatsapp'].get('lastError'),
        'googleSlackCheckedAt':updated['sync'].get('checkedAt'),
        'automaticWhatsAppSyncVerified':updated['whatsapp']['automaticSyncVerified']}))
