import json,sys
from pathlib import Path
from update import ROOT,SITE,atomic,export
def merge_reports(previous,incoming):
    assert incoming['store']['id']==819567008
    result=dict(incoming)
    result['reports']=dict(previous.get('reports',{}))
    result['reportCheckedAt']={k:previous.get('reportCheckedAt',{}).get(k,previous.get('checkedAt')) for k in result['reports']}
    result['errors']=dict(incoming.get('errors',{}))
    for key in ['today','yesterday','month','daily']:
        report=incoming.get('reports',{}).get(key)
        if isinstance(report,dict) and isinstance(report.get('rows'),list) and key not in result['errors']:
            result['reports'][key]=report
            result['reportCheckedAt'][key]=incoming['checkedAt']
        else:
            result['errors'].setdefault(key,'تعذر تحديث التقرير؛ آخر نسخة ناجحة محفوظة بتاريخها الأصلي.')
    return result

if __name__=='__main__':
    incoming=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    path=ROOT/'local/b2c-data.json'
    previous=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    d=merge_reports(previous,incoming)
    atomic(path,json.dumps(d,ensure_ascii=False))
    current=json.loads((SITE/'data.json').read_text(encoding='utf-8'))
    export(current)
    print('B2C imported: '+d['checkedAt'])
