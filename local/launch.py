"""Desktop entry point using the bundled Python runtime; no PowerShell required."""
import argparse,json,subprocess,sys,time,urllib.request,webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8765/'
def healthy():
    try:
        with urllib.request.urlopen(URL+'health',timeout=2) as response:
            return json.load(response).get('app')=='ceo-followup-local'
    except (OSError,ValueError):return False

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    if not healthy():
        runtime=Path(sys.executable).with_name('python.exe')
        with (ROOT/'local/desktop-server.log').open('ab') as out:
            subprocess.Popen([str(runtime),'-X','utf8',str(ROOT/'local/server.py')],cwd=ROOT,
                stdin=subprocess.DEVNULL,stdout=out,stderr=out,creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(20):
            if healthy():break
            time.sleep(.25)
        else:raise RuntimeError('Local dashboard did not start. Open Codex to repair it.')
    if not args.no_browser:webbrowser.open(URL,new=2)
    return URL

if __name__=='__main__':
    try:
        result=main()
        if sys.stdout:print(result)
    except Exception as exc:
        (ROOT/'local/desktop-launch-error.log').write_text(str(exc),encoding='utf-8')
        if sys.stderr:print(str(exc),file=sys.stderr)
        raise SystemExit(1)
