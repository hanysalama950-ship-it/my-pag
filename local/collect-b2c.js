// Execute in functions.exec, not Node. Authenticated Salla reads only.
const context=await tools.mcp__codex_apps__salla_store_context_get({});
if(context.isError||context.structuredContent?.store?.data?.id!==819567008)throw new Error('Unexpected Salla store; keep previous snapshot');
const d={checkedAt:new Date().toISOString(),store:{id:819567008,name:'EMIZ',currency:'SAR'},reports:{},errors:{},dailyComplete:false,dailyNote:'جدول يومي للنتائج التي أتاحها تقرير سلة؛ اكتمال الصفحات غير متحقق.'};
const jobs=[['today',()=>tools.mcp__codex_apps__salla_reports_sales_summary({period:'today'})],['yesterday',()=>tools.mcp__codex_apps__salla_reports_sales_summary({period:'yesterday'})],['month',()=>tools.mcp__codex_apps__salla_reports_sales_summary({period:'this_month'})],['daily',()=>tools.mcp__codex_apps__salla_reports_orders_daily({period:'this_month',_limit:50})]];
const settled=await Promise.allSettled(jobs.map(async([key,fn])=>{const r=await fn();if(r.isError||!Array.isArray(r.structuredContent?.rows))throw new Error('Report unavailable: '+key);d.reports[key]=r.structuredContent;}));
settled.forEach((r,i)=>{if(r.status==='rejected')d.errors[jobs[i][0]]=String(r.reason);});
if(!Object.keys(d.reports).length)throw new Error('All Salla reports failed; retain last snapshot and report failure');
const expenseCode=await tools.exec_command({cmd:'Get-Content D:/EMIZ/ceo-project/local/collect-b2c-expenses.js -Raw',max_output_tokens:6000});
try{if(expenseCode.exit_code!==0)throw new Error('Expense collector unavailable');await new (Object.getPrototypeOf(async function(){}).constructor)('tools','text',expenseCode.output)(tools,text);}catch(e){d.errors.expenses=String(e);}
const path='D:/EMIZ/work/b2c-'+Date.now()+'.json';
text(await tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(d)+'\n*** End Patch'));
const result=await tools.exec_command({cmd:"& 'C:/Users/HQ_2026_QH/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 'D:/EMIZ/ceo-project/local/import-b2c.py' '"+path+"'",max_output_tokens:300});
text(result);if(result.exit_code!==0)throw new Error('B2C import failed');
