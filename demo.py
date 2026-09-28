#!/usr/bin/env python3
"""Run the two-PR failure in temporary local Git repositories."""
import argparse
import contextlib
import io
import unittest
from tests.test_guard import GuardTests
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--lang",choices=["en","fr","es"],default="en")
 args=parser.parse_args()
 lines={
  "en":["1. PR A is merged while the agent's checkout stays old.","2. Task B is blocked before its worktree is created.","3. After a fast-forward, task B starts with PR A present."],
  "fr":["1. La PR A est fusionnée ; le checkout de l'agent reste ancien.","2. La tâche B est bloquée avant création de son worktree.","3. Après une avance rapide, B démarre avec la PR A présente."],
  "es":["1. Se fusiona la PR A; el checkout del agente sigue antiguo.","2. La tarea B se bloquea antes de crear su worktree.","3. Tras avanzar la rama local, B arranca con la PR A incluida."],
 }
 with contextlib.redirect_stdout(io.StringIO()):
  result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.TestSuite([GuardTests("test_stale_checkout_blocks_creation_and_fresh_checkout_succeeds")]))
 if result.wasSuccessful(): print("\n".join(lines[args.lang]))
 else: print(result.errors or result.failures)
 raise SystemExit(0 if result.wasSuccessful() else 1)
