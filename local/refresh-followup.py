"""Refresh only follow-up sheet sources from saved connector responses."""
import copy, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import update

inbox = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
data = json.loads((update.SITE/'data.json').read_text(encoding='utf-8'))
before = copy.deepcopy(data)
backup = update.ROOT.parent/'archive'/'before-sheet-refresh-20260930'
backup.mkdir(parents=True, exist_ok=True)
for path in [update.SITE/'data.json', update.SITE/'data.js', update.ROOT/'dashboard.html', update.ROOT/'sources.json']:
    target = backup/path.name
    if not target.exists(): target.write_bytes(path.read_bytes())
checked = inbox['checkedAt']
summary = {}
for key in ['tasks', 'archive']:
    source = next(s for s in data['sources'] if s['id']==key)
    records, excluded, date = update.tasks(inbox['inputs'][key], source['url'], key=='archive')
    old_titles = {r['title'] for r in before.get(key, [])}
    summary[key] = {'before':len(before.get(key, [])), 'after':len(records), 'added':[r['title'] for r in records if r['title'] not in old_titles]}
    data[key] = records
    if key=='tasks':
        data['taskReportDate']=date
        source['sourceDate']=date
        source['details']='قراءة تبويب المتابعة؛ تاريخ التقرير داخل المصدر: '+date
    else: data['archiveExcluded']=excluded
    source.update(syncStatus='ok', status='read', lastCheckedAt=checked, lastSuccessAt=checked)
    source.pop('syncError', None)
data['snapshotDate']=datetime.fromisoformat(checked.replace('Z','+00:00')).astimezone(timezone(timedelta(hours=3))).date().isoformat()
data['sync']['revision']=checked
data['sync']['errors']=sum(s.get('syncStatus')=='error' for s in data['sources'])
data['sync']['lastFollowupRefreshAt']=checked
update.export(data)
saved=json.loads((update.SITE/'data.json').read_text(encoding='utf-8'))
assert saved['tasks']==data['tasks']
for source in before['sources']:
    if source['id'] not in ['tasks','archive']:
        assert source==next(s for s in saved['sources'] if s['id']==source['id'])
for key in ['teams','hiring','collection','sales','reports','whatsapp']:
    assert before.get(key)==saved.get(key), key
assert all(r['title'] in (update.ROOT/'dashboard.html').read_text(encoding='utf-8') for r in saved['tasks'])
print(json.dumps({'checkedAt':checked, 'changes':summary, 'verified':True},ensure_ascii=False))
