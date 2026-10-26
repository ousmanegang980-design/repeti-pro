"""RépétiPro — cycle sauvegarde : export -> effacement -> restauration vérifiée (§20.16)."""
import os, sys, tempfile
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/index.html"
ok = ko = 0
def check(nom, cond, detail=""):
    global ok, ko
    if cond: ok += 1; print("✅ " + nom)
    else: ko += 1; print("❌ " + nom + (" — " + str(detail) if detail else ""))

profil = tempfile.mkdtemp(prefix="repetipro-restore-")
dls = tempfile.mkdtemp(prefix="repetipro-dl-")
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(profil, headless=True, accept_downloads=True)
    page = ctx.new_page(); page.goto(BASE); page.wait_for_selector("#kpis .kpi")
    # Données de démo (3 élèves, paiements, reçus)
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="parametres"]')
    page.click("#btnDemo")
    page.wait_for_function("document.querySelector('#kpis') && document.querySelector('#kpis').innerText.includes('3')")
    check("Démonstration chargée (3 élèves)", True)
    # Export
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="synchro"]')
    with page.expect_download() as dl: page.click("#btnExport")
    sauvegarde = os.path.join(dls, "sauvegarde.json"); dl.value.save_as(sauvegarde)
    # Effacement total
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="parametres"]')
    page.click("#btnReset"); page.wait_for_selector("#cfOk"); page.click("#cfOk")
    page.wait_for_function("document.querySelector('#kpis .kpi .v') && document.querySelector('#kpis .kpi .v').innerText.trim() === '0'")
    check("Après effacement : tableau de bord à 0 élève actif", page.inner_text("#kpis .kpi .v").strip() == "0", page.inner_text("#kpis").replace(chr(10), " | "))
    # Restauration (la validation interne vérifie la somme de contrôle AVANT tout remplacement)
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="synchro"]')
    page.set_input_files("#fileImport", sauvegarde)
    page.wait_for_selector("#cfOk"); page.click("#cfOk")
    page.wait_for_function("document.querySelector('#importResultat').innerText.includes('Restauration réussie')")
    check("Restauration réussie (message confirmé)", True)
    page.click('[data-nav="dashboard"]')
    check("Après restauration : 3 élèves retrouvés", "\n3\n" in "\n" + page.inner_text("#kpis") + "\n")
    # Sauvegarde corrompue rejetée
    corr = os.path.join(dls, "corrompue.json")
    open(corr, "w", encoding="utf-8").write(open(sauvegarde, encoding="utf-8").read().replace("25000", "99999", 1))
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="synchro"]')
    page.set_input_files("#fileImport", corr)
    page.wait_for_function("document.querySelector('#importResultat').innerText.length > 0")
    txt = page.inner_text("#importResultat")
    check("Sauvegarde corrompue REJETÉE, données intactes", "contrôle" in txt or "corrompu" in txt, txt)
    ctx.close()
print(f"\nRésultat restauration : {ok} réussis, {ko} échoués.")
sys.exit(1 if ko else 0)
