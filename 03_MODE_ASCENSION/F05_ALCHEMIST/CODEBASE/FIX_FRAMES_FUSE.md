# FIX — Frames non sauvegardées sur Drive (bug FUSE Playwright)

## Problème

Lors du render, Flask indique `"status": "DONE"` et déclare N frames traitées,
mais le dossier `OUT_FRAMES` sur Google Drive reste vide.

### Cause racine

Playwright (Chromium headless) s'exécute dans un subprocess sandboxé.
Ce subprocess **ne peut pas écrire directement sur le mount FUSE Google Drive**
(`/content/drive/MyDrive/...`).

L'appel `page.screenshot(path="/content/drive/...")` ne lève pas d'exception,
mais le fichier n'est jamais créé. Le process Python parent peut écrire sur Drive
(le test `shutil` réussit), mais pas le subprocess Chromium.

### Symptôme de confirmation

```
Statut Flask: DONE
Frames déclarées: 100 / 100
Dossier existe mais VIDE : /content/drive/MyDrive/EXODUS_V3/M3/F05_ALCHEMIST/OUT_FRAMES
Drive monté ? True
Ecriture sur Drive : OK   ← Python peut écrire, pas Chromium
```

---

## Fix appliqué dans `m3_f05_flask.py`

Deux étapes au lieu d'une :

1. Playwright écrit chaque frame en **local** (`/content/frames_out/`)
2. Python copie immédiatement vers Drive via `shutil.copy2()`

```python
# AVANT (ne fonctionne pas — FUSE inaccessible depuis Chromium)
page.screenshot(path=str(OUT_FRAMES / fname), full_page=False)

# APRÈS (fonctionnel)
local_path = LOCAL_FRAMES / fname                         # /content/frames_out/
page.screenshot(path=str(local_path), full_page=False)   # Playwright → local
if local_path.exists():
    shutil.copy2(str(local_path), str(OUT_FRAMES / fname))  # Python → Drive
```

La variable `LOCAL_FRAMES = Path("/content/frames_out")` est déclarée en tête de fichier.

---

## Comment appliquer ce fix dans une session Colab

Colle cette cellule **avant** de lancer la Cell 3 (Flask) :

```python
# ═══════════════════════════════════════════════════════════════
# PATCH CELL — FIX FRAMES FUSE  (à exécuter avant Cell 3)
# ═══════════════════════════════════════════════════════════════
import urllib.request, shutil
from pathlib import Path

CODEBASE = Path("/content/drive/MyDrive/EXODUS_V2/03_MODE_ASCENSION/F05_ALCHEMIST/CODEBASE")
LOCAL    = Path("/content/m3_f05")

URL_FLASK = (
    "https://raw.githubusercontent.com/kioka8877-ux/EXODUS-V2"
    "/mescouilles/03_MODE_ASCENSION/F05_ALCHEMIST/CODEBASE/m3_f05_flask.py"
)

# Télécharger la version patchée depuis la branche mescouilles
CODEBASE.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(URL_FLASK, CODEBASE / "m3_f05_flask.py")

# Si Flask est déjà copié en local, patcher aussi
if LOCAL.exists():
    shutil.copy2(str(CODEBASE / "m3_f05_flask.py"), str(LOCAL / "m3_f05_flask.py"))

print("Fix FUSE frames appliqué — relance Cell 3.")
```

Ensuite :
1. **Cell 3** — relancer Flask (important : redémarrer pour charger le nouveau flask)
2. Lancer un render de test **10 frames**
3. Vérifier `EXODUS_V3/M3/F05_ALCHEMIST/OUT_FRAMES/` dans Drive

---

## Notes

- Les frames locales restent dans `/content/frames_out/` pendant la session Colab
- Si la session Colab reboot, `/content/frames_out/` disparaît mais les copies Drive sont préservées
- Le checkpoint (`m3_f05_checkpoint.json`) permet de reprendre un render interrompu depuis la dernière frame sauvegardée
