# -*- coding: utf-8 -*-
"""Fusionne repetipro/ en UN seul fichier HTML autonome : /home/user/index.html"""
import urllib.parse, os
base = "/home/user/repetipro"
html = open(f"{base}/index.html", encoding="utf-8").read()
css = open(f"{base}/styles.css", encoding="utf-8").read()
logic = open(f"{base}/logic.js", encoding="utf-8").read()
app = open(f"{base}/app.js", encoding="utf-8").read()
icon = open(f"{base}/icon.svg", encoding="utf-8").read()
for nom, contenu in [("logic.js", logic), ("app.js", app), ("styles.css", css)]:
    assert "</script" not in contenu.lower(), f"{nom} contient </script> : fusion unsafe"

html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', "")
html = html.replace('<link rel="icon" href="icon.svg" type="image/svg+xml">',
                    '<link rel="icon" href="data:image/svg+xml,' + urllib.parse.quote(icon) + '">')
html = html.replace('<link rel="stylesheet" href="styles.css">', "<style>\n" + css + "\n</style>")
# Pas de sw.js en monofichier : on neutralise l'enregistrement du Service Worker
app = app.replace('if ("serviceWorker" in navigator && location.protocol.startsWith("http")) navigator.serviceWorker.register("sw.js").catch(() => {});',
                  '/* Monofichier GitHub : pas de Service Worker externe ; les données restent en IndexedDB (persistant). Pour le cache hors-ligne complet, utilisez la version multi-fichiers. */')
html = html.replace('<script src="logic.js"></script>', "<script>\n" + logic + "\n</script>")
html = html.replace('<script src="app.js"></script>', "<script>\n" + app + "\n</script>")
entete = """<!--
  ═══════════════════════════════════════════════════════════════════════
  RépétiPro — FICHIER UNIQUE prêt pour GitHub Pages
  1) Créez un dépôt GitHub (ex. "repetipro")
  2) Déposez CE fichier sous le nom : index.html
  3) Settings → Pages → Deploy from a branch → main → Save
  4) Ouvrez l'URL fournie par GitHub sur le téléphone (Chrome Android)
  Données : stockées sur l'appareil (IndexedDB). Exportez des sauvegardes !
  ═══════════════════════════════════════════════════════════════════════
-->
"""
out = "/home/user/index.html"
open(out, "w", encoding="utf-8").write(entete + html)
print("OK :", out, os.path.getsize(out), "octets — 1 seul fichier, aucune dépendance")
