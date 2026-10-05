"""Record the schedule created and verified through the Codex automation tool."""
import json
from pathlib import Path
from update import export
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'site/data.json').read_text(encoding='utf-8'))
data['sync'].update(enabled=True,automationId='automation',revision=data['sync']['checkedAt']+'-active')
export(data)
(root/'local/sync-state.json').write_text(json.dumps({'automationId':'automation','lastCheckedAt':data['sync']['checkedAt'],'errors':[],'knownLimitations':['Sales is best-effort readable text.','Calls metadata only; attachment metrics unavailable.']},ensure_ascii=False,indent=2),encoding='utf-8')
