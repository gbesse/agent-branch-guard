import subprocess,tempfile,unittest
from pathlib import Path
from guard import inspect,main

def run(*args):
 p=subprocess.run(args,capture_output=True,text=True,check=True)
 return p.stdout.strip()

class GuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name)
  self.remote,self.local,self.other=(root/x for x in ("remote.git","local","other"))
  run("git","init","--bare",str(self.remote));run("git","clone",str(self.remote),str(self.local))
  for repo,name in [(self.local,"Demo")]:
   run("git","-C",str(repo),"config","user.name",name);run("git","-C",str(repo),"config","user.email","demo@example.test")
  (self.local/"first.txt").write_text("first\n")
  run("git","-C",str(self.local),"add",".");run("git","-C",str(self.local),"commit","-m","initial")
  run("git","-C",str(self.local),"branch","-M","main");run("git","-C",str(self.local),"push","-u","origin","main")
  run("git","clone","-b","main",str(self.remote),str(self.other))
  run("git","-C",str(self.other),"config","user.name","Reviewer");run("git","-C",str(self.other),"config","user.email","reviewer@example.test")
 def tearDown(self): self.tmp.cleanup()
 def advance_remote(self):
  (self.other/"merged.txt").write_text("merged PR A\n")
  run("git","-C",str(self.other),"add",".");run("git","-C",str(self.other),"commit","-m","merged A");run("git","-C",str(self.other),"push","origin","main")
 def test_stale_checkout_blocks_creation_and_fresh_checkout_succeeds(self):
  self.assertEqual(inspect(self.local,"origin/main")["status"],"ready")
  self.advance_remote();self.assertEqual(inspect(self.local,"origin/main")["status"],"stale_local")
  path=self.local.parent/"agent-b"
  self.assertEqual(main(["create","--repo",str(self.local),"--branch","agent-b","--path",str(path),"--json"]),2)
  self.assertFalse(path.exists())
  run("git","-C",str(self.local),"pull","--ff-only","origin","main")
  self.assertEqual(main(["create","--repo",str(self.local),"--branch","agent-b","--path",str(path),"--json"]),0)
  self.assertEqual((path/"merged.txt").read_text(),"merged PR A\n")
 def test_queued_base_moved_even_after_local_sync(self):
  expected=inspect(self.local,"origin/main")["observed_base"]
  self.advance_remote();run("git","-C",str(self.local),"pull","--ff-only","origin","main")
  self.assertEqual(inspect(self.local,"origin/main",expected)["status"],"queued_base_moved")
if __name__=="__main__":unittest.main()
