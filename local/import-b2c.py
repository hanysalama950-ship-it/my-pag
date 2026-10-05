import json,sys
from pathlib import Path
from update import ROOT,SITE,atomic,export
d=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
assert d['store']['id']==819567008
for key,report in d['reports'].items():
    assert isinstance(report.get('rows'),list),key
atomic(ROOT/'local/b2c-data.json',json.dumps(d,ensure_ascii=False))
current=json.loads((SITE/'data.json').read_text(encoding='utf-8'))
export(current)
print('B2C imported: '+d['checkedAt'])
