// Execute inside functions.exec. Reads only the named B2C channel and its dated text reports.
function unwrap(r){if(r.isError)throw new Error('Slack read failed');return r.structuredContent||JSON.parse(r.content.find(x=>x.type==='text').text);}
const channel=unwrap(await tools.mcp__codex_apps__slack_slack_read_channel({channel_id:'C0B40S4G14P',limit:100,response_format:'detailed'}));
const entries=[];
const today=new Date(Date.now()+10800000).toISOString().slice(0,10);
const yesterday=new Date(Date.parse(today+'T12:00:00Z')-86400000).toISOString().slice(0,10);
for(const block of channel.messages.split('=== Message from ')){
 const ts=block.match(/Message TS: ([\d.]+)/)?.[1];if(!ts)continue;
 for(const m of block.matchAll(/(\d{2})-(\d{2})-(\d{4})\.txt \(ID: (F\w+),/g)){
  const date=m[3]+'-'+m[2]+'-'+m[1];
  if(date.slice(0,7)!==today.slice(0,7)&&date!==yesterday)continue;
  entries.push({date,fileId:m[4],ts});
 }
}
const rows=[],errors=[];
const results=await Promise.allSettled(entries.map(async e=>{
 const f=unwrap(await tools.mcp__codex_apps__slack_slack_read_file({file_id:e.fileId}));
 const daily=f.text_content?.match(/^DAILY\s*\|[^\n]*?(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\s*\n([\s\S]*?)(?=^(?:WEEKLY|MONTHLY|CUMULATIVE)\s*\||$(?![\s\S]))/m);
 if(!daily||daily[1]!==e.date||daily[2]!==e.date)throw new Error('Unrecognized daily period: '+e.fileId);
 const matches=[...daily[3].matchAll(/^Total Ad Spend\s*\|\s*SAR\s+([\d,]+(?:\.\d+)?)\s*\|/gm)];
 if(matches.length!==1)throw new Error('Ambiguous total: '+e.fileId);
 const spend=Number(matches[0][1].replaceAll(',',''));if(!Number.isFinite(spend)||spend<0)throw new Error('Invalid spend');
 rows.push({...e,spend,url:'https://al-rossaisgroup.slack.com/archives/C0B40S4G14P/p'+e.ts.replace('.','')});
}));
results.forEach((r,i)=>{if(r.status==='rejected')errors.push({date:entries[i].date,error:String(r.reason)});});
const byDate={};for(const r of rows.sort((a,b)=>Number(a.ts)-Number(b.ts)))byDate[r.date]=r;
for(const e of errors)delete byDate[e.date];
const snapshot={checkedAt:new Date().toISOString(),rows:Object.values(byDate).sort((a,b)=>a.date.localeCompare(b.date)),errors,scope:'آخر 100 رسالة؛ الملفات النصية المؤرخة للشهر الحالي. أحدث تقرير لكل يوم، دون المجاميع الأسبوعية والتراكمية.'};
if(!rows.length&&errors.length)throw new Error('Expense import failed; preserve snapshot');
text(await tools.apply_patch('*** Begin Patch\n*** Add File: D:/EMIZ/ceo-project/local/b2c-expenses.json\n+'+JSON.stringify(snapshot)+'\n*** End Patch'));
