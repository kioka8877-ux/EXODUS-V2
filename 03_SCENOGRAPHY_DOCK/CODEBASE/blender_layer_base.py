#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   BLENDER LAYER BASE — Classe de base partagée pour les Layer Builders      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Centralise la logique commune Blender (collections, gestion erreurs)       ║
║  partagée entre dome_builder, glass_builder et shadow_catcher_builder.      ║
║                                                                              ║
║  Décret II — Codex Imperial v6 — 23.04.2026                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy


class BlenderLayerBuilder:
    """
    Classe de base pour les constructeurs de couches Blender (Layer Builders).

    Fournit les utilitaires communs :
      - _ensure_collection() : création/récupération de collection Blender
      - _tag          : préfixe de log par sous-classe
    """

    _tag: str = "LAYER"

    @staticmethod
    def _ensure_collection(name: str) -> bpy.types.Collection:
        """
        Crée ou récupère une collection Blender par nom et la linke à la scène.

        Si la collection existe déjà, la retourne sans modification.
        Sinon, la crée et la linke à bpy.context.scene.collection.

        Args:
            name: Nom de la collection.

        Returns:
            La collection Blender (existante ou nouvellement créée).
        """
        if name in bpy.data.collections:
            return bpy.data.collections[name]
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
        return coll
