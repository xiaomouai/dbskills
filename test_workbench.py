import json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT=Path(__file__).with_name("workbench.py")
class WorkbenchTest(unittest.TestCase):
    def cli(self,root,*args,ok=True):
        p=subprocess.run([sys.executable,str(SCRIPT),"--root",str(root),*args],text=True,capture_output=True)
        if ok:self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        return p
    def test_full_flow_and_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.cli(root,"init"); self.cli(root,"init")
            self.cli(root,"plan","--request","测试 <获客>","--mode","full","--track","business")
            self.assertNotEqual(self.cli(root,"plan","--request","重复",ok=False).returncode,0)
            self.assertNotEqual(self.cli(root,"start","strategy",ok=False).returncode,0)
            self.assertIn("&lt;获客&gt;",(root/"index.html").read_text())
            self.assertNotEqual(self.cli(root,"complete","research","--output","../bad.md",ok=False).returncode,0)
            for task in ("research","strategy","content","sales","delivery","review"):
                self.cli(root,"start",task); out=root/"artifacts"/f"{task}.md"; out.write_text(task)
                self.cli(root,"complete",task,"--output",f"artifacts/{task}.md")
            self.cli(root,"verify")
            data=json.loads((root/"tasks.json").read_text()); self.assertTrue(all(t["status"]=="completed" for t in data["tasks"]))
    def test_verify_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.cli(root,"plan","--request","x","--mode","diagnose","--track","consumer")
            self.assertEqual(self.cli(root,"verify",ok=False).returncode,1)
if __name__=="__main__":unittest.main()
