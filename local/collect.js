// Run this file's contents in functions.exec, where authenticated connector tools exist.
// This is orchestration code for the local Codex heartbeat, not a browser/Node script.
const base = 'D:/EMIZ';
const python = 'C:/Users/HQ_2026_QH/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const inbox = {checkedAt:new Date().toISOString(),inputs:{},errors:{}};
function unwrap(r){
  if(r.isError)throw new Error('Connector returned an error');
  if(r.structuredContent)return r.structuredContent;
  const raw=r.content?.find(x=>x.type==='text')?.text;
  if(!raw)throw new Error('Empty connector result');
  return JSON.parse(raw);
}
async function capture(key,fn){try{inbox.inputs[key]=await fn();}catch(e){inbox.errors[key]=String(e.message||e);}}
async function values(id,title,range){return unwrap(await tools.mcp__codex_apps__google_drive_get_spreadsheet_range({spreadsheet_id:id,sheet_name:title,range}));}
function tab(meta,id){const p=meta.sheets.find(s=>s.properties.sheetId===id)?.properties;if(!p||p.gridProperties.rowCount>8000)throw new Error('Sheet schema needs review');return p;}
function column(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
async function sheets(){
  const id='1cRqADbYSr9xMgs2IXMEPIVj6GokDC8Zt_19uHz_tt1I';
  try{
    const meta=unwrap(await tools.mcp__codex_apps__google_drive_get_spreadsheet_metadata({spreadsheet_id:id}));
    await Promise.allSettled([['tasks',0,'F'],['archive',281417223,'E']].map(([key,gid,col])=>capture(key,async()=>{const p=tab(meta,gid);return values(id,p.title,'A1:'+col+p.gridProperties.rowCount);}))); 
  }catch(e){inbox.errors.tasks=inbox.errors.archive=String(e.message);}
}
async function hiring(){
  const id='1zgluTTLz2H8Wm0XtCb16pz_HJisOGhmCJmfAyZ9RB6A';
  try{
    const meta=unwrap(await tools.mcp__codex_apps__google_drive_get_spreadsheet_metadata({spreadsheet_id:id}));
    const p=tab(meta,1240866926);
    const header=await values(id,p.title,'A1:'+column(p.gridProperties.columnCount-1)+'1');
    const names=header.values[0].map(x=>String(x||'').trim());
    const a=names.indexOf('الاسم'),b=names.indexOf('التوصية النهائية');
    if(a<0||b<0)throw new Error('Hiring columns changed');
    await Promise.allSettled([['hiringNames',a],['hiringRecommendations',b]].map(([key,i])=>capture(key,()=>values(id,p.title,column(i)+'1:'+column(i)+p.gridProperties.rowCount))));
  }catch(e){inbox.errors.hiring=String(e.message);}
}
async function list(id){
  const pages=[];let cursor='';const seen=new Set();
  do{
    const page=unwrap(await tools.mcp__codex_apps__slack_slack_read_list({list_id:id,format:'csv',limit:100,...(cursor?{cursor}:{})}));
    if(typeof page.result!=='string'||!page.result.startsWith('Record ID,'))throw new Error('Invalid Slack list');
    pages.push(page);cursor=page.next_cursor||'';
    if(cursor&&seen.has(cursor))throw new Error('Repeated Slack cursor');
    seen.add(cursor);
    if(pages.length>=80&&cursor)throw new Error('List exceeds configured read scope');
  }while(cursor);
  return {pages};
}
async function sales(){
  const meta=unwrap(await tools.mcp__codex_apps__google_drive_get_file_metadata({fileId:'1jLI5Ns2sJ9niJUMwO-a8tC7LCrr6Oz7H',fields:'id,name,mimeType,modifiedTime'}));
  const file=unwrap(await tools.mcp__codex_apps__google_drive_fetch({url:'https://docs.google.com/spreadsheets/d/1jLI5Ns2sJ9niJUMwO-a8tC7LCrr6Oz7H/edit'}));
  if(typeof file.content!=='string')throw new Error('Missing readable sales text');
  return {content:file.content,modifiedTime:meta.modified_time||meta.modifiedTime};
}
const channelJobs=Object.entries({'marketing-channel':'C0C1KG3UE3B','creative-channel':'C0C0G8QGBSS','team-marketing-channel':'C0B0901QXSA'}).map(([key,id])=>capture(key,async()=>unwrap(await tools.mcp__codex_apps__slack_slack_read_channel({channel_id:id,limit:100,response_format:'detailed'}))));
const jobs=[...channelJobs,sheets(),hiring(),capture('sales',sales),...Object.entries({collection:'F0BFR86EYJY',marketing:'F0C2BUTGNJC',creative:'F0BB6KV7N3U',cx:'F0BD4EG8ZNW'}).map(([key,id])=>capture(key,()=>list(id))),...Object.entries({orders:'C0B04N23NAX',calls:'C0C06E5AZ32'}).map(([key,id])=>capture(key,async()=>unwrap(await tools.mcp__codex_apps__slack_slack_read_channel({channel_id:id,limit:10}))))];
const settled=await Promise.allSettled(jobs);
for(const r of settled)if(r.status==='rejected')inbox.errors.orchestration=String(r.reason);
inbox.checkedAt=new Date().toISOString();
const inputPath=base+'/work/sync-inbox-'+Date.now()+'.json';
const patch=await tools.apply_patch('*** Begin Patch\n*** Add File: '+inputPath+'\n+'+JSON.stringify(inbox)+'\n*** End Patch');
if(patch?.isError)throw new Error('Could not save connector results');
const result=await tools.exec_command({cmd:"& '"+python+"' -X utf8 '"+base+"/ceo-project/local/update.py' '"+inputPath+"' --consume",workdir:base,max_output_tokens:1500});
text(result);
if(result.exit_code!==0)throw new Error('Dashboard update failed');
text(await tools.exec_command({cmd:"& '"+base+"/ceo-project/Start-Dashboard.ps1' -NoBrowser",workdir:base,max_output_tokens:300}));
