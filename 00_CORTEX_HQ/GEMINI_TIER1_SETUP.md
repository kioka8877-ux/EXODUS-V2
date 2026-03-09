# ⚡ GEMINI API — Activation Tier 1 (Gratuit)

> Guide opérationnel pour débloquer les vrais quotas Gemini sans dépenser un centime.

---

## 🎯 Pourquoi Tier 1 ?

| | Free Tier | Tier 1 |
|---|---|---|
| **RPM** (requêtes/min) | 15 | **4 000** |
| **RPD** (requêtes/jour) | 1 000 | **14 000** |
| **TPM** (tokens/min) | 250K | **4M** |

**Free Tier = inutilisable** pour U00 CORTEX. L'analyse vidéo multi-frames envoie des dizaines de requêtes en rafale → tu tapes le `429 Resource Exhausted` en quelques secondes.

**Tier 1 = 200x plus large**, et toujours gratuit. Google ne prélève rien tant que tu restes dans les quotas gratuits. La carte bancaire sert uniquement de vérification d'identité.

### ⚠️ Modèle cible

- `gemini-2.0-flash` → **DÉPRÉCIÉ** depuis mars 2026, retiré de l'API
- `gemini-2.5-flash-lite` → **modèle par défaut** (déjà configuré dans `EXO_00_CORTEX.py`)

---

## ✅ Prérequis

- Un compte Google (Gmail suffit)
- Une carte bancaire (prépayée type Revolut, N26, Wise = OK)
- 10 minutes

---

## ÉTAPE 1 — 🔑 Récupérer ta clé API

> 🔗 https://aistudio.google.com/apikey

1. Se connecter sur [aistudio.google.com](https://aistudio.google.com)
2. Menu gauche → **"Get API Key"**
3. Cliquer **"Create API key"** → **"Create API key in new project"**
4. Copier la clé (commence par `AIzaSy...`)
5. **Noter le nom du projet** associé — tu en auras besoin à l'Étape 2

---

## ÉTAPE 2 — 💳 Lier un compte de facturation (Tier 1)

> 🔗 https://console.cloud.google.com/billing

1. Aller sur [console.cloud.google.com/billing](https://console.cloud.google.com/billing)
2. En haut à gauche : **sélectionner le même projet** que ta clé API
3. Cliquer **"Link a billing account"**
4. Si pas de compte existant : **"Create billing account"** → suivre le wizard
5. Entrer une carte bancaire (prépayée type Revolut = OK)
6. Cliquer **"Link"**

> ⚠️ **Tu ne seras PAS prélevé** tant que tu ne dépasses pas les quotas gratuits.
> La carte sert uniquement à vérifier que tu es un humain — c'est ce qui déverrouille le Tier 1.

---

## ÉTAPE 3 — 🛡️ Configurer une alerte budget $0

> 🔗 https://console.cloud.google.com/billing/budgets

1. Menu **"Budgets & alerts"** dans la section Billing
2. Cliquer **"Create budget"**
3. Nommer le budget (ex: `EXODUS-safety`)
4. Amount = **$0**
5. Cocher **"Email alerts"** à **100%**
6. Sauvegarder

> 💡 Filet de sécurité absolu : tu reçois un mail si le moindre centime est facturé.

---

## ÉTAPE 4 — 🔍 Vérifier ton Tier

> 🔗 https://aistudio.google.com/apikey

1. Retourner sur [AI Studio](https://aistudio.google.com/apikey)
2. Sur ta clé, vérifier la mention **"Pay as you go"** ou **"Tier 1"**
3. Si encore **"Free"** → attendre 5 min puis rafraîchir la page

> 💡 La propagation prend parfois jusqu'à 10 minutes après le lien billing.

---

## ÉTAPE 5 — 🔐 Configurer la clé sur Colab (Secrets)

### Option A — Secrets Colab (recommandé) ✅

```python
# 1. Dans Colab : icône 🔑 (panneau gauche) → "Add new secret"
# 2. Name: GOOGLE_API_KEY
# 3. Value: ta_clé_AIzaSy...
# 4. Activer "Notebook access"

from google.colab import userdata
import os
os.environ["GOOGLE_API_KEY"] = userdata.get("GOOGLE_API_KEY")
print("✅ Clé chargée")
```

### Option B — Variable directe (rapide, moins sécurisé)

```python
import os
os.environ["GOOGLE_API_KEY"] = "AIzaSy...ta_clé..."  # ⚠️ Ne jamais commit ce fichier
```

---

## ÉTAPE 6 — 🧪 Tester avec gemini-2.5-flash-lite

```python
import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash-lite")

response = model.generate_content("Dis juste OK")
print(f"✅ SUCCÈS — Réponse : {response.text.strip()}")
print("Tier 1 actif — U00 CORTEX prêt à tourner.")
```

**Résultat attendu :**
```
✅ SUCCÈS — Réponse : OK
Tier 1 actif — U00 CORTEX prêt à tourner.
```

**Si erreur :**
- `429 Resource Exhausted` → retourner à l'**Étape 2** (billing pas encore lié)
- `404 Not Found` → vérifier le nom du modèle = `gemini-2.5-flash-lite`

---

## 📊 Quotas comparatifs

| Modèle | Tier | RPM | RPD | TPM |
|--------|------|-----|-----|-----|
| `gemini-2.0-flash` | **DÉPRÉCIÉ** | — | — | — |
| `gemini-2.5-flash-lite` | Free | 15 | 1 000 | 250K |
| **`gemini-2.5-flash-lite`** | **Tier 1** | **4 000** | **14 000** | **4M** |
| `gemini-2.5-flash` | Tier 1 | 2 000 | 10 000 | 4M |

---

## 🔧 Troubleshooting

| Erreur | Cause | Fix |
|--------|-------|-----|
| `429 Resource Exhausted` | Free tier ou IP partagée | Activer billing Tier 1 (Étape 2) |
| `404 Model not found` | Mauvais nom de modèle | Utiliser `gemini-2.5-flash-lite` |
| `403 API not enabled` | API Gemini pas activée | console.cloud.google.com → APIs → activer **"Generative Language API"** |
| `401 Invalid API key` | Clé incorrecte ou expirée | Régénérer sur [aistudio.google.com](https://aistudio.google.com/apikey) |
| Toujours `429` après Tier 1 | Propagation en cours | Attendre 10 min et retester |

---

## 🚀 Lancer U00 après activation

```bash
python EXO_00_CORTEX.py \
  --drive-root /content/drive/MyDrive/EXODUS_V2 \
  --input-video test_brookhaven_10s.mp4
# Le modèle gemini-2.5-flash-lite est maintenant le défaut
```

---

> 📎 Ce guide fait partie de [EXODUS-V2](../README.md) — Unit 00 CORTEX HQ
