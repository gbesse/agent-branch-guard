#!/usr/bin/env python3
"""Verify a coding agent's Git base before it creates a worktree."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

MESSAGES = {
 "en": {"ready":"Ready: local HEAD matches the fetched base.","stale_local":"Blocked: local HEAD differs from the fetched base.","queued_base_moved":"Blocked: the base moved since this task was queued.","created":"Worktree created from the verified base.","review_ready":"Ready: this branch contains the fetched base.","invalid_expected":"Expected base must be a full commit SHA.","base_missing":"Blocked: this branch does not contain the fetched base.","error":"Could not verify the base."},
 "fr": {"ready":"Prêt : HEAD local correspond à la base récupérée.","stale_local":"Bloqué : HEAD local diffère de la base récupérée.","queued_base_moved":"Bloqué : la base a changé depuis la mise en file de cette tâche.","created":"Worktree créé depuis la base vérifiée.","review_ready":"Prêt : cette branche contient la base récupérée.","invalid_expected":"La base attendue doit être un SHA de commit complet.","base_missing":"Bloqué : cette branche ne contient pas la base récupérée.","error":"Impossible de vérifier la base."},
 "es": {"ready":"Listo: HEAD local coincide con la base obtenida.","stale_local":"Bloqueado: HEAD local difiere de la base obtenida.","queued_base_moved":"Bloqueado: la base cambió desde que se puso en cola la tarea.","created":"Worktree creado desde la base verificada.","review_ready":"Listo: esta rama contiene la base obtenida.","invalid_expected":"La base esperada debe ser un SHA de commit completo.","base_missing":"Bloqueado: esta rama no contiene la base obtenida.","error":"No se pudo verificar la base."},
}

def git(repo:Path,*args:str)->str:
 p=subprocess.run(["git","-C",str(repo),*args],capture_output=True,text=True,timeout=30)
 if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "git failed")
 return p.stdout.strip()

def inspect(repo:Path,base:str,expected:str|None=None,fetch:bool=True,review:bool=False)->dict:
 if "/" not in base or base.startswith("/"): raise ValueError("base must be REMOTE/BRANCH, for example origin/main")
 remote,branch=base.split("/",1)
 if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*",remote) or not branch or branch.startswith("-"):
  raise ValueError("base must be REMOTE/BRANCH")
 if expected is not None and not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}",expected):
  raise ValueError("invalid_expected")
 expected=expected.lower() if expected is not None else None
 git(repo,"check-ref-format",f"refs/heads/{branch}")
 if fetch: git(repo,"fetch","--no-tags",remote,f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}")
 local=git(repo,"rev-parse","HEAD")
 observed=git(repo,"rev-parse",f"refs/remotes/{remote}/{branch}")
 contains_base=int(git(repo,"rev-list","--count",observed,"--not",local))==0 if review else local==observed
 ahead_by=int(git(repo,"rev-list","--count",f"{observed}..{local}")) if contains_base else None
 status="queued_base_moved" if expected and expected!=observed else ("base_missing" if review else "stale_local") if not contains_base else "ready"
 return {"status":status,"base":base,"local_head":local,"observed_base":observed,"expected_base":expected,"observed_at":datetime.now(timezone.utc).isoformat(),"fetched":fetch,"mode":"review" if review else "bootstrap","contains_base":contains_base,"ahead_by":ahead_by}

def main(argv:list[str]|None=None)->int:
 parser=argparse.ArgumentParser(description="Prove the Git base before an AI agent starts a worktree.")
 parser.add_argument("action",choices=["check","create","review"])
 parser.add_argument("--repo",default=".")
 parser.add_argument("--base",default="origin/main",help="remote/branch to fetch and compare")
 parser.add_argument("--expected",help="base SHA recorded when the task was queued")
 parser.add_argument("--lang",choices=MESSAGES,default="en")
 parser.add_argument("--offline",action="store_true",help="use existing remote-tracking ref; less safe")
 parser.add_argument("--branch",help="new worktree branch (create only)")
 parser.add_argument("--path",help="new worktree path (create only)")
 parser.add_argument("--json",action="store_true",help="print a machine-readable receipt")
 args=parser.parse_args(argv); repo=Path(args.repo).resolve()
 try:
  if args.action=="create" and (not args.branch or not args.path): raise ValueError("create requires --branch and --path")
  result=inspect(repo,args.base,args.expected,not args.offline,args.action=="review")
  if result["status"]=="ready" and args.action=="create":
   path=Path(args.path).resolve()
   if path.exists(): raise ValueError("worktree path already exists")
   git(repo,"worktree","add","-b",args.branch,str(path),result["observed_base"])
   actual=git(path,"rev-parse","HEAD")
   if actual!=result["observed_base"]: raise RuntimeError("worktree base changed during creation")
   result.update(status="created",worktree=str(path),branch=args.branch)
 except (ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
  detail=str(exc)
  result={"status":"error","detail":MESSAGES[args.lang].get(detail,detail)}
 if args.json: print(json.dumps(result,sort_keys=True))
 else:
  print(MESSAGES[args.lang]["review_ready" if args.action=="review" and result["status"]=="ready" else result["status"]])
  if result["status"] in {"ready","stale_local","queued_base_moved","base_missing","created"}: print(f"local={result['local_head'][:12]} fetched={result['observed_base'][:12]}")
  if result.get("detail"): print(result["detail"],file=sys.stderr)
 return 0 if result["status"] in {"ready","created"} else 2 if result["status"] in {"stale_local","queued_base_moved","base_missing"} else 1

if __name__=="__main__": raise SystemExit(main())
