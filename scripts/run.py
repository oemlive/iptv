import os,sys,subprocess
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); p=subprocess.run([sys.executable,R+"/scripts/fetch_hw.py"])
if p.returncode: raise SystemExit(p.returncode)
subprocess.check_call([sys.executable,R+"/scripts/process.py"])
