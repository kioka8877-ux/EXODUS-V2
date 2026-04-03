# TRACKING_WEAPONS — Registre des Armes de Vulkan

> Responsable : VULKAN_FORGE (exception VOX)
> Mis a jour lors de l'ajout de chaque nouvelle weapon.

---

## Registre

| Weapon | Statut | Role | Usage | Date |
|--------|--------|------|-------|------|
| test_runner.py | OPERATIONNEL | Teste les scripts de l'Arsenal (syntaxe + structure) | `python test_runner.py --all` | 2026-04-03 |
| diff_analyzer.py | OPERATIONNEL | Analyse les differences entre deux versions d'un fichier | `python diff_analyzer.py <avant> <apres>` | 2026-04-03 |
| sentinel_bridge.py | OPERATIONNEL | Interface VULKAN_FORGE <-> SENTINEL_CORE | `python sentinel_bridge.py <fregate_path>` | 2026-04-03 |
| hook_dispatcher.py | OPERATIONNEL | Dispatcher d'evenements entre Tech-Pretres | `python hook_dispatcher.py <event> <payload>` | 2026-04-03 |

---

## Events Disponibles (hook_dispatcher)

| Event | Declencheur | Action |
|-------|-------------|--------|
| `fix.applied` | Apres application d'un fix | Log dans ledger |
| `fregate.validated` | Apres validation d'une fregate | Notification |
| `arsenal.updated` | Apres ajout dans Arsenal | Log |
| `session.start` | Debut de session Vulkan | Chargement contexte |

---

## Prochaines Weapons Potentielles

- `blender_probe.py` — Interroger Blender headless sur une scene
- `render_validator.py` — Valider qu'un render produit des frames valides
