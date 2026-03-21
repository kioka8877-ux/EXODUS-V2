# Note au Sigillite — U03 `geometry_probe_u03.py` (Session Vulkan)

**Destinataire :** Malcador le Sigillite  
**Objet :** Ce qui a été livré sur `main` et comment l’utiliser sans répéter les erreurs de diagnostic.

---

## 1. Contexte

Des vérifications U03 basées uniquement sur le **nombre de vertices bruts** (`len(mesh.vertices)`) ont conduit à des **faux diagnostics** : avec **Subdivision + Displace non appliqués**, le mesh d’édition peut rester à **4 vertices** alors que le rendu évalue une géométrie bien plus dense.

**Principe retenu (ATOM-IC / premiers principes) :** valider la pile **modificateurs** + **vertices évalués** (depsgraph), et écrire un **rapport JSON sur disque** — **ne pas** parser `stdout` Blender pour du JSON (bannières, logs mélangés → `json.loads` impossible).

---

## 2. Livrables fusionnés dans `main`

| Élément | Chemin |
|--------|--------|
| Script probe headless | `03_SCENOGRAPHY_DOCK/CODEBASE/geometry_probe_u03.py` |
| Doc unité | `03_SCENOGRAPHY_DOCK/UNIT_03_SUBPLAN.md` (section *Diagnostic géométrie*) |
| Notebook Colab | `03_SCENOGRAPHY_DOCK/CODEBASE/EXO_03_GEOMETRY_PROBE.ipynb` |
| Cette note | `TRACKING/MALCADOR_NOTE_U03_GEOMETRY_PROBE.md` |

**Branche d’origine :** `feature/u03-geometry-probe` — intégrée à **`main`** (merge + push).

---

## 3. Comportement du script

- Lance Blender en `--background` sur un `.blend` (ex. `environment_1.blend`).
- Pour chaque mesh : vertices **bruts**, vertices **évalués** (depsgraph), liste des **modificateurs** (SUBSURF/DISPLACE + détails utiles).
- Statut logique pour U03 : recherche d’un objet dont le nom contient `displacement` ; attendu **SUBSURF + DISPLACE** pour marquer une situation cohérente avec le pipeline Tri-Layer.
- Sortie : **fichier JSON** (`--output` ou `GEOMETRY_PROBE_OUT`).

**Ce que ça ne fait pas :** juger la beauté du rendu, l’exposition Filmic, ou la présence d’une caméra U04 — ce sont d’autres portes (U04 / rendu).

---

## 4. Lien GitHub direct (notebook)

```
https://github.com/kioka8877-ux/EXODUS-V2/blob/main/03_SCENOGRAPHY_DOCK/CODEBASE/EXO_03_GEOMETRY_PROBE.ipynb
```

Sur Colab : **Fichier → Ouvrir un notebook → GitHub** → coller l’URL du repo ou importer le fichier depuis Drive après `git pull`.

---

## 5. Recommandation opérationnelle

1. Après génération des `environment_*.blend`, exécuter la probe (notebook ou CLI).
2. Si `status` ≠ attendu : inspecter `notes` et la liste `modifiers` pour `displacement_mesh` **avant** d’attribuer les noirs de rendu uniquement à U03.
3. Conserver le JSON dans `OUT_PREMIUM_SCENE/` ou `TRACKING/` pour traçabilité Marshal.

---

## 6. Synthèse une ligne

**`geometry_probe_u03.py` = contrat de vérité machine-lisible sur la géométrie U03 (modifs + évaluation), sans se fier au seul comptage brut de vertices.**

---

*Fin de transmission — Vulkan*
