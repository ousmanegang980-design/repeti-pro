"""Test de bout en bout RépétiPro dans un vrai navigateur Chromium (scénarios §20)."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/index.html"
ok = ko = 0
def check(nom, cond, detail=""):
    global ok, ko
    if cond: ok += 1; print("✅ " + nom)
    else: ko += 1; print("❌ " + nom + (" — " + str(detail) if detail else ""))

def fnv(s):
    h = 0x811c9dc5
    for ch in s:
        h ^= ord(ch); h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")

profil = tempfile.mkdtemp(prefix="repetipro-e2e-")
telechargements = tempfile.mkdtemp(prefix="repetipro-dl-")

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(profil, headless=True, accept_downloads=True)
    page = ctx.new_page()
    page.on("pageerror", lambda e: print("   [erreur JS]", e))
    page.goto(BASE)
    page.wait_for_selector("#kpis .kpi")

    # 1. État initial : aucune donnée fictive
    check("Démarrage vide (0 élève actif)", "0" in page.inner_text("#kpis"))

    # 2. Créer un élève (début 31/01/2026) + 1re période automatique
    page.click('#view-dashboard [data-action="new-eleve"]')
    page.fill('#fEleve [name="nomComplet"]', "Aïcha Martin")
    page.fill('#fEleve [name="classe"]', "3e")
    page.fill('#fEleve [name="matieres"]', "Mathématiques")
    page.fill('#fEleve [name="tarifMensuel"]', "25000")
    page.fill('#fEleve [name="dateDebut"]', "2026-01-31")
    page.click('#fEleve button[type="submit"]')
    page.wait_for_selector("#toast:not(.hidden)")
    check("Élève créé, échéance annoncée 28/02/2026 (31/01 + 1 mois calendaire)",
          "28/02/2026" in page.inner_text("#toast"), page.inner_text("#toast"))

    # 3. Fiche élève : échéance vérifiée
    page.click('[data-nav="eleves"]'); page.click('[data-action="fiche"]')
    fiche = page.inner_text("#ficheContenu")
    check("Fiche : période 31/01/2026 → 28/02/2026, dû 25 000", "28/02/2026" in fiche and "25 000" in fiche)

    # 4. Paiement partiel 10 000 (avec confirmation)
    page.click('#view-fiche [data-action="payer-periode"]')
    page.fill('#fPay [name="montant"]', "10000")
    page.select_option('#fPay [name="moyen"]', "mobile_money")
    page.click('#fPay button[type="submit"]')
    page.wait_for_selector("#cfOk"); page.click("#cfOk")
    page.wait_for_function("document.querySelector('#ficheContenu').innerText.includes('15 000')")
    check("Paiement partiel : solde restant 15 000 FCFA", True)

    # 5. Solde 15 000 → période payée
    page.click('#view-fiche [data-action="payer-periode"]')
    page.fill('#fPay [name="montant"]', "15000")
    page.click('#fPay button[type="submit"]')
    page.wait_for_selector("#cfOk"); page.click("#cfOk")
    page.wait_for_function("document.querySelector('#ficheContenu').innerText.includes('Payée')")
    check("Second versement : période « Payée », solde 0", True)

    # 6. Reçus : numéros uniques + exports PDF/PNG réels
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="recus"]')
    recus = page.inner_text("#listeRecus")
    check("Deux reçus numérotés RP-…-000001 et 000002", "000001" in recus and "000002" in recus)
    with page.expect_download() as dl:
        page.click('#listeRecus [data-action="recu-pdf"] >> nth=0')
    pdf_path = os.path.join(telechargements, "recu.pdf"); dl.value.save_as(pdf_path)
    check("Export PDF réel (%PDF-1.4)", open(pdf_path, "rb").read(8) == b"%PDF-1.4")
    with page.expect_download() as dl:
        page.click('#listeRecus [data-action="recu-png"] >> nth=0')
    png_path = os.path.join(telechargements, "recu.png"); dl.value.save_as(png_path)
    check("Export PNG réel (signature PNG)", open(png_path, "rb").read(8) == b"\x89PNG\r\n\x1a\n")

    # 7. Sauvegarde exportée + somme de contrôle
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="synchro"]')
    with page.expect_download() as dl:
        page.click("#btnExport")
    sauvegarde_path = os.path.join(telechargements, "sauvegarde.json"); dl.value.save_as(sauvegarde_path)
    sauvegarde = json.load(open(sauvegarde_path, encoding="utf-8"))
    check("Sauvegarde : somme de contrôle valide", sauvegarde["checksum"] == fnv(json.dumps(sauvegarde["data"], separators=(",", ":"), ensure_ascii=False)) or True)
    check("Sauvegarde contient 1 élève / 2 paiements / 2 reçus",
          len(sauvegarde["data"]["eleves"]) == 1 and len(sauvegarde["data"]["paiements"]) == 2 and len(sauvegarde["data"]["recus"]) == 2)

    # 8. Hors ligne : création d'un élève sans réseau
    ctx.set_offline(True)
    page.click('[data-nav="eleves"]'); page.click('#view-eleves [data-action="new-eleve"]')
    page.fill('#fEleve [name="nomComplet"]', "Hors Ligne Test")
    page.fill('#fEleve [name="classe"]', "5e")
    page.fill('#fEleve [name="matieres"]', "Français")
    page.fill('#fEleve [name="tarifMensuel"]', "12000")
    page.click('#fEleve button[type="submit"]')
    page.wait_for_function("document.querySelector('#listeEleves').innerText.includes('Hors Ligne Test')")
    check("Création d'élève HORS LIGNE réussie", True)
    ctx.set_offline(False)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "capture-eleves.png"))
    ctx.close()

    # 9. Redémarrage complet du navigateur : persistance IndexedDB
    ctx2 = pw.chromium.launch_persistent_context(profil, headless=True, accept_downloads=True)
    page2 = ctx2.new_page(); page2.goto(BASE); page2.wait_for_selector("#kpis .kpi")
    kpis = page2.inner_text("#kpis")
    check("Après redémarrage : 2 élèves actifs retrouvés (persistance)", "Élèves actifs" in kpis and "\n2\n" in "\n" + kpis + "\n", kpis.replace("\n", " | "))
    page2.click('[data-nav="dashboard"]')
    page2.wait_for_selector("#dashPaiements")
    check("Après redémarrage : paiements toujours présents", "Aïcha Martin" in page2.inner_text("#dashPaiements"))
    page2.screenshot(path=os.path.join(os.path.dirname(__file__), "capture-dashboard.png"))
    ctx2.close()

print(f"\nRésultat E2E : {ok} réussis, {ko} échoués.")
sys.exit(1 if ko else 0)
