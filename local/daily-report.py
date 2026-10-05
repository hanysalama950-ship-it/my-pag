"""Create a dated, source-grounded daily briefing. This script never sends messages."""
import argparse, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from update import ROOT, SITE, atomic, export

RIYADH=timezone(timedelta(hours=3))
def build(data, now, preview=False):
    day=now.date().isoformat()
    groups={}
    seen=set()
    def add(department,title):
        title=' '.join(title.split()).strip()
        signature=(department,title)
        if title and signature not in seen:
            seen.add(signature)
            groups.setdefault(department,[]).append(title)
    from daily_review import validate
    review=validate(data,day)
    data['_dailyReview']=review
    for item in review['items']:
        add(item['department'],item['title'])
    if not review['complete']:
        # Only dated completion evidence belongs in a daily accomplishments message.
        for task in data.get('archive',[]):
            if task.get('source')=='whatsapp' and task.get('reportDate')==day:
                add(task.get('department','المهام المباشرة'),task['title'])
        for task in data.get('tasks',[]):
            if task.get('status')=='تم الإنجاز' and task.get('completedAt','')[:10]==day:
                add('المهام المباشرة',task['title'])
        # Marketing end is explicitly the source's completion-date column.
        # Creative end dates and CX complaint dates are not completion evidence.
        for task in data.get('teams',{}).get('marketing',[]):
            if task.get('rawStatus','').lower()=='done' and task.get('end')==day:
                add('التسويق',task['title'])
    for task in data.get('marketingCompleted',[]):
        if task.get('completionDate')==day:
            add('التسويق',task['title'])
    from operations import summary, DEPARTMENT
    # Shipping is represented once using the dated source report.
    for department in list(groups):
        groups[department]=[t for t in groups[department] if not ('تجهيز' in t and 'شحن' in t)]
        if not groups[department]: del groups[department]
    for line in summary(data,now): add(DEPARTMENT,line)
    lines=['السلام عليكم أ. مهند،']
    for department,items in groups.items():
        lines.extend(['',department+':'])
        lines.extend('• '+title for title in items)
    if not groups:
        lines.extend(['','لم تتوفر حتى الآن مهام مكتملة موثقة بتاريخ اليوم.'])
    return '\n'.join(lines)+'\n',stale_sources(data,now)

def stale_sources(data,now):
    stale=[]
    for source in data.get('sources',[]):
        try: age=(now-datetime.fromisoformat(source['lastSuccessAt'].replace('Z','+00:00'))).total_seconds()/60
        except (KeyError,ValueError,TypeError): age=float('inf')
        if age>60 or source.get('syncStatus')=='error':stale.append(source.get('area',source['id']))
    return stale

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');args=parser.parse_args()
    now=datetime.now(RIYADH);data=json.loads((SITE/'data.json').read_text(encoding='utf-8'))
    review_path=ROOT/'local'/('daily-completions-'+now.date().isoformat()+'.json')
    if review_path.exists():
        data['dailyCompletions']=json.loads(review_path.read_text(encoding='utf-8'))
    text,stale=build(data,now,args.preview)
    folder=ROOT/'daily-reports';folder.mkdir(exist_ok=True)
    name=('preview-' if args.preview else 'daily-')+now.date().isoformat()
    atomic(folder/(name+'.txt'),text)
    atomic(folder/(name+'.md'),text)
    atomic(folder/('latest-preview.txt' if args.preview else 'latest.txt'),text)
    record={'date':now.date().isoformat(),'generatedAt':now.isoformat(),'preview':args.preview,
            'text':text,'staleSources':stale,'scheduleHour':18,'timezone':'Asia/Riyadh',
            'sourceReviewComplete':data['_dailyReview']['complete'],
            'reviewIssues':data['_dailyReview']['issues'],
            'reviewedSourceCount':len(data['_dailyReview']['reviewedSourceIds']),
            'sourceCount':len(data.get('sources',[])),
            'sourceSnapshotAt':data.get('sync',{}).get('checkedAt')}
    data.pop('_dailyReview',None)
    atomic(folder/(name+'.json'),json.dumps(record,ensure_ascii=False,indent=2))
    data['dailyReport']=record
    data['sync']['revision']=now.isoformat()
    export(data)
    if not args.preview:
        state_path=ROOT/'local/daily-report-state.json'
        state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
        state.update({'lastGeneratedDate':now.date().isoformat(),'lastGeneratedAt':now.isoformat(),'lastResult':'generated','reportFile':str(folder/(name+'.txt'))})
        atomic(state_path,json.dumps(state,ensure_ascii=False,indent=2))
    print(json.dumps({'report':str(folder/(name+'.txt')),'preview':args.preview,'staleSources':len(stale),'characters':len(text)},ensure_ascii=False))

if __name__=='__main__':main()
