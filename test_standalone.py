# -*- coding: utf-8 -*-
"""Test du monofichier /home/user/index.html + capture du nouveau reçu pro."""
import os, sys, tempfile
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8766/index.html"
profil = tempfile.mkdtemp(prefix="rp-standalone-"); dls = tempfile.mkdtemp(prefix="rp-dl-")
erreurs = []
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(profil, headless=True, accept_downloads=True,
                                                viewport={"width": 420, "height": 860})
    page = ctx.new_page()
    page.on("pageerror", lambda e: erreurs.append(str(e)))
    page.goto(BASE); page.wait_for_selector("#kpis .kpi")
    assert "404" not in page.title(), page.title()
    # Paramètres : entreprise + slogan
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="parametres"]')
    page.fill("#pActivite", "Académie Réussite Plus")
    page.fill("#pSlogan", "La réussite à portée de main")
    page.fill("#pTel", "+228 90 12 34 56"); page.fill("#pCoords", "Lomé – Bè, Togo")
    page.click('#formParams button[type="submit"]')
    page.wait_for_selector("#toast:not(.hidden)")
    # Démo -> génère de vrais paiements + reçus avec l'en-tête entreprise
    page.click("#btnDemo")
    page.wait_for_function("document.querySelector('#kpis').innerText.includes('3')")
    # Reçus : aperçu + PNG
    page.click('[data-nav="plus"]'); page.click('#menuPlus [data-nav="recus"]')
    page.wait_for_selector('#listeRecus [data-action="voir-recu"]')
    with page.expect_download() as dl:
        page.click('#listeRecus [data-action="recu-png"] >> nth=0')
    png = os.path.join(dls, "recu-pro.png"); dl.value.save_as(png)
    with page.expect_download() as dl:
        page.click('#listeRecus [data-action="recu-pdf"] >> nth=0')
    pdf = os.path.join(dls, "recu-pro.pdf"); dl.value.save_as(pdf)
    page.click('#listeRecus [data-action="voir-recu"] >> nth=0')
    page.wait_for_selector(".recu-aperçu")
    aperçu = page.inner_text(".recu-aperçu")
    page.wait_for_timeout(400)
    page.screenshot(path="/home/user/repetipro/tests/capture-recu-pro.png")
    ok_nom = "Académie Réussite Plus" in aperçu and "La réussite" in aperçu
    ok_png = open(png, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    ok_pdf = open(pdf, "rb").read(8) == b"%PDF-1.4"
    import shutil; shutil.copy(png, "/home/user/repetipro/tests/recu-pro.png"); shutil.copy(pdf, "/home/user/repetipro/tests/recu-pro.pdf")
    print("✅ Monofichier chargé sans erreur JS" if not erreurs else "❌ Erreurs JS: " + str(erreurs))
    print(("✅" if ok_nom else "❌") + " Nom d'entreprise + slogan sur le reçu")
    print(("✅" if ok_png else "❌") + " PNG du nouveau reçu")
    print(("✅" if ok_pdf else "❌") + " PDF du nouveau reçu")
    ctx.close()
    sys.exit(0 if (ok_nom and ok_png and ok_pdf and not erreurs) else 1)
