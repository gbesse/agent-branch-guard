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
 def test_review_accepts_new_commits_but_bootstrap_does_not(self):
  (self.local/"feature.txt").write_text("feature\n")
  run("git","-C",str(self.local),"add",".");run("git","-C",str(self.local),"commit","-m","feature")
  result=inspect(self.local,"origin/main",review=True)
  self.assertEqual(result["status"],"ready");self.assertEqual(result["ahead_by"],1)
  self.assertEqual(inspect(self.local,"origin/main")["status"],"stale_local")
 def test_review_blocks_branch_missing_new_remote_commits_then_accepts_merge(self):
  (self.local/"feature.txt").write_text("feature\n")
  run("git","-C",str(self.local),"add",".");run("git","-C",str(self.local),"commit","-m","feature")
  self.advance_remote()
  self.assertEqual(inspect(self.local,"origin/main",review=True)["status"],"base_missing")
  run("git","-C",str(self.local),"merge","--no-edit","origin/main")
  self.assertEqual(inspect(self.local,"origin/main",review=True)["status"],"ready")
 def test_review_queued_receipt_takes_precedence_and_rejects_short_sha(self):
  expected=inspect(self.local,"origin/main")["observed_base"]
  self.advance_remote()
  self.assertEqual(inspect(self.local,"origin/main",expected,review=True)["status"],"queued_base_moved")
  with self.assertRaises(ValueError):inspect(self.local,"origin/main",expected[:8])
 def test_review_blocks_unrelated_history(self):
  run("git","-C",str(self.local),"checkout","--orphan","unrelated")
  run("git","-C",str(self.local),"commit","-m","unrelated")
  self.assertEqual(inspect(self.local,"origin/main",review=True)["status"],"base_missing")
 def test_review_cli_languages(self):
  import contextlib,io
  for lang in ("fr","en","es"):
   with contextlib.redirect_stdout(io.StringIO()) as out:
    self.assertEqual(main(["review","--repo",str(self.local),"--lang",lang]),0)
   self.assertTrue(out.getvalue().strip())
if __name__=="__main__":unittest.main()
