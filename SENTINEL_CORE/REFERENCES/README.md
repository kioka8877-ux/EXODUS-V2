# REFERENCES — DNA Samples SENTINEL B8

Dossier des references parfaites par fregate.
Ces fichiers servent de "reponse connue" pour l'ingenierie inverse.

## Structure

```
REFERENCES/
├── U03/
│   ├── sample_01_input.png        ← depth map (l'equation)
│   └── sample_01_output.blend     ← scene parfaite (la reponse)
├── U04/
│   ├── sample_01_input.blend      ← scene brute
│   └── sample_01_output.png       ← frame parfaite
└── README.md                      ← ce fichier
```

## Comment ajouter une reference

1. Identifier un output VALIDE d'une fregate
2. Copier l'input et l'output dans le bon dossier U0X/
3. Nommer : sample_01, sample_02, etc.
4. SENTINEL B8 utilisera ces paires pour calibrer les parametres

## Statut

| Fregate | Samples | Statut |
|---------|---------|--------|
| U03 | 0 | A alimenter apres validation |
| U04 | 0 | A alimenter apres test 10 frames |
| U05 | 0 | Phase 3 |
