"""Update B2B only using a saved read-only Drive response."""
import copy, json, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import update

inbox=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
data=json.loads((update.SITE/'data.json').read_text(encoding='utf-8'))
before=copy.deepcopy(data)
checked=inbox['checkedAt']
today=datetime.fromisoformat(checked.replace('Z','+00:00')).astimezone(timezone(timedelta(hours=3))).date().isoformat()
sales=update.sales(inbox,today)
backup=update.ROOT.parent/'archive'/('before-b2b-'+checked.replace(':','').replace('.',''))
backup.mkdir(parents=True,exist_ok=True)
for path in [update.SITE/'data.json',update.SITE/'data.js',update.ROOT/'dashboard.html',update.ROOT/'sources.json']:
    (backup/path.name).write_bytes(path.read_bytes())
data['sales']=sales
s=next(s for s in data['sources'] if s['id']=='sales')
s.update(lastCheckedAt=checked,lastSuccessAt=checked,syncStatus='partial',status='read',details=sales['scope']+(' إجمالي التحصيل غير مكتمل؛ توجد قيمة غير رقمية.' if not sales['collectionsComplete'] else ''))
s.pop('syncError',None)
data['snapshotDate']=today
data['sync'].update(revision=checked,lastSalesRefreshAt=checked)
data['sync']['errors']=sum(s.get('syncStatus')=='error' for s in data['sources'])
update.export(data)
saved=json.loads((update.SITE/'data.json').read_text(encoding='utf-8'))
assert saved['sales']==sales
for key in ['tasks','teams','hiring','collection','reports','whatsapp']:
    assert before.get(key)==saved.get(key),key
for source in before['sources']:
    if source['id']!='sales': assert source==next(s for s in saved['sources'] if s['id']==source['id'])
html=(update.ROOT/'dashboard.html').read_text(encoding='utf-8')
assert 'التحصيل الرقمي فقط — غير مكتمل' in html
print(json.dumps({'beforeInvoices':len(before['sales']['invoices']),'invoices':len(sales['invoices']),'gross':sales['gross'],'units':sales['units'],'collectionsTotal':sales['collectionsTotal'],'invalidCollections':sales['invalidCollections'],'latestInvoice':max(r['date'] for r in sales['invoices']),'verified':True},ensure_ascii=False))
