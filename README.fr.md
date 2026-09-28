# Agent Branch Guard

**Empêche un agent de code d'annuler une PR déjà fusionnée.** Avant une nouvelle tâche, ce petit outil récupère la branche cible et vérifie que le checkout local pointe encore sur elle. Il refuse de créer un worktree depuis un ancien commit.

Français · [English](README.md) · [Español](README.es.md)

## Voir l'échec en une commande

```sh
python3 demo.py
```

La démo hors ligne crée un dépôt distant temporaire et deux clones. Un clone fusionne la modification A. Le checkout ancien de l'agent tente de lancer B : **blocage avant création du worktree**. Après une avance rapide, B démarre avec A déjà présente. Aucun compte, modèle, clé API ni service réseau n'est nécessaire.

## Utiliser sur votre dépôt

```sh
python3 guard.py check --repo /chemin/vers/depot --base origin/main --lang fr
python3 guard.py create --repo /chemin/vers/depot --base origin/main \
  --branch agent-tache-b --path /chemin/vers/agent-tache-b --lang fr
```

Codes de sortie : `0` prêt/créé ; `2` HEAD local ou base mise en file périmée ; `1` erreur Git/configuration. `--json` imprime un reçu avec les SHA local et récupéré ainsi que l'heure d'observation. Enregistrer le SHA lors de la mise en file, puis passer `--expected SHA` au lancement ; la tâche est bloquée si la branche distante a changé entre-temps. `--lang es` fournit les messages en espagnol.

**Portée :** le `HEAD` local doit être identique à la branche distante fraîchement récupérée. Les commits locaux en avance sont également refusés : il faut les examiner ou les pousser avant de créer le worktree. La branche distante peut bouger après le fetch ; le reçu atteste le SHA utilisé, pas un verrou permanent. `--offline` saute le fetch et ne prouve pas la fraîcheur.

## Projets voisins

- [Agent Office #119](https://github.com/AgentSystemLabs/agent-office/issues/119) décrit une seconde PR d'agent qui annule la première après un départ depuis un `HEAD` local périmé. La démo reproduit ce scénario.
- [Worktrunk](https://github.com/max-sixty/worktrunk) gère les worktrees Git pour des agents parallèles. Agent Branch Guard se limite à prouver le commit de départ. Aucune intégration ni affiliation n'est revendiquée.
- [Un retour sur les worktrees Claude Code](https://www.reddit.com/r/ClaudeCode/comments/1uwmz32/psa_claude_code_creates_subagent_worktrees_from/) décrit un autre écart entre commits locaux et base distante choisie. La comparaison stricte des SHA détecte aussi ce cas.

## Tester

```sh
python3 -m unittest discover -s tests -v
```

Python 3.11+, Git ; aucune dépendance Python. MIT. Outil alpha en ligne de commande, sans intégration avec Agent Office ou Worktrunk. Il ne fusionne, ne tire ni ne pousse à votre place.
