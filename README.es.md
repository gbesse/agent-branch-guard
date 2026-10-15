# Agent Branch Guard

**Evita que un agente de programación deshaga una PR ya fusionada.** Antes de iniciar una tarea nueva, esta pequeña herramienta obtiene la rama de destino y comprueba que el checkout local aún apunta a ella. Se niega a crear un worktree desde un commit antiguo.

[Français](README.fr.md) · [English](README.md) · Español

## Ver el fallo con un comando

```sh
python3 demo.py
```

La demostración sin conexión crea un remoto temporal y dos clones. Un clon fusiona el cambio A. El checkout antiguo del agente intenta iniciar B: **se bloquea antes de crear el worktree**. Tras avanzar la rama local, B arranca con A incluida. No hace falta cuenta, modelo, clave API ni servicio de red.

## Usarlo en tu repositorio

```sh
python3 guard.py check --repo /ruta/al/repositorio --base origin/main --lang es
python3 guard.py create --repo /ruta/al/repositorio --base origin/main \
  --branch agente-tarea-b --path /ruta/a/agente-tarea-b --lang es
```

Códigos de salida: `0` listo/creado; `2` HEAD local o base de tarea obsoleta; `1` error de Git/configuración. `--json` imprime un comprobante con los SHA local y obtenido y la hora de observación. Guarda el SHA al poner la tarea en cola y pasa `--expected SHA` al iniciarla; la tarea se bloquea si el remoto cambió entretanto. `--lang fr` ofrece mensajes en francés.

**Alcance:** el `HEAD` local debe coincidir con la rama remota recién obtenida. También se rechazan los commits locales adelantados: revísalos o súbelos antes de crear el worktree. El remoto puede avanzar después del fetch; el comprobante registra el SHA usado, no bloquea permanentemente la rama. `--offline` omite el fetch y no demuestra actualidad.

## Proyectos relacionados

- [Agent Office #119](https://github.com/AgentSystemLabs/agent-office/issues/119) describe una segunda PR de agente que revierte la primera tras partir de un `HEAD` local obsoleto. La demostración reproduce ese caso.
- [Worktrunk](https://github.com/max-sixty/worktrunk) gestiona worktrees Git para agentes paralelos. Agent Branch Guard solo demuestra el commit de inicio. No se afirma ninguna integración ni afiliación.
- [Un informe sobre worktrees de Claude Code](https://www.reddit.com/r/ClaudeCode/comments/1uwmz32/psa_claude_code_creates_subagent_worktrees_from/) describe otra diferencia entre commits locales y la base remota elegida. La comparación estricta de SHA también detecta ese caso.

## Pruebas

```sh
python3 -m unittest discover -s tests -v
```

Python 3.11+, Git; sin paquetes Python. MIT. Herramienta alfa de línea de comandos, sin integración con Agent Office ni Worktrunk. No fusiona, descarga cambios ni sube commits por ti.

## Comprobar la rama terminada antes de revisión

```sh
python3 guard.py review --repo /ruta/feature --base origin/main --json --lang es
```

`review` obtiene la base y acepta commits locales de funcionalidad solo si la base obtenida pertenece a la ascendencia de `HEAD`. Una rama sin un commit recién integrado en la base termina con `2` y `base_missing`; integre o rebase deliberadamente y vuelva a comprobar. El recibo contiene `contains_base`, `ahead_by` (commits accesibles solo desde HEAD) y los SHA observados. `--expected` exige un SHA completo y sigue bloqueando una base en cola que ha cambiado. `check` y `create` conservan su igualdad estricta. Esta comprobación de ascendencia no detecta reversiones semánticas, no sustituye la revisión, no demuestra un árbol limpio ni bloquea el remoto después de obtenerlo.
