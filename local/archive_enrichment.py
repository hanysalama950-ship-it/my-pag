"""Project-only archive enrichment; no writes to WhatsApp, Sheets, or Slack."""
import hashlib
import json
import re
from pathlib import Path

def normalized(value):
    return re.sub(r'\s+', ' ', value).strip()

def enrich(data):
    path = Path(__file__).with_name('whatsapp-classifications.json')
    if not path.exists():
        return
    spec = json.loads(path.read_text(encoding='utf-8'))
    if spec.get('reviewed') is not True:
        raise ValueError('WhatsApp classification must be reviewed before archive import')
    reports = data.get('whatsapp', {}).get('reports', [])
    added, seen = [], set()
    for report in reports:
        classified = []
        for item in spec.get('byDate', {}).get(report['messageDate'], []):
            quote = normalized(item['evidence'])
            if quote not in normalized(report['text']):
                continue
            if item.get('state') != 'completed':
                continue
            identity = hashlib.sha256((report['messageDate']+'\n'+quote).encode()).hexdigest()[:24]
            if identity in seen:
                continue
            seen.add(identity)
            task = dict(id='wa-task-'+identity, title=item['title'],
                owner='', department=item['department'], due=report['messageDate'],
                reportDate=report['messageDate'], dateBasis='تاريخ التقرير المرسل، وليس موعد تسليم',
                priority='', status='مكتملة حسب التقرير', source='whatsapp',
                sourceReportId=report['id'], evidence=item['evidence'],
                note=item['department']+' · واتساب · '+report['messageDate']+' · الدليل: '+item['evidence'],
                url='https://web.whatsapp.com/')
            if report.get('validationWarnings'):
                task['note'] += ' · '+ ' '.join(report['validationWarnings'])
            classified.append(task)
            added.append(task)
        report['classifiedCompleted'] = classified
    data['archive'] = sorted(added, key=lambda r:r['reportDate'], reverse=True) + [
        r for r in data['archive'] if r.get('source') != 'whatsapp']
    data['whatsapp']['archiveCount'] = len(added)
    data['whatsapp']['archiveScope'] = spec['scope']
    data['whatsapp']['classificationNote'] = 'الأرشفة للأفعال المنجزة الصريحة فقط. البنود الجارية والمخططة والحالات الوصفية محفوظة في نصوص التقارير ولا تُحسب مكتملة. قد يرد العمل نفسه في مصادر أخرى؛ الأعداد سجلات وليست إنجازات فريدة عبر المصادر.'
