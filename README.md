# RépétiPro — « Tes élèves, tes paiements, zéro oubli. »

Application **offline-first** de gestion des répétitions, des échéances mensuelles et des paiements,
pour répétiteurs indépendants, professeurs particuliers et petits centres de soutien (contexte initial : Togo, FCFA).

Version 1.0 — **PWA (Progressive Web App) installable sur Android**, sans aucune dépendance externe :
tout fonctionne hors ligne, les reçus PDF sont générés par le code de l'app (PDF 1.4 écrit nativement),
les images PNG via Canvas, les données dans **IndexedDB** (persistant après fermeture/redémarrage).

---

## 1. Lancer l'application

### Option A — Téléphone (recommandée)
1. Hébergez le dossier `repetipro/` sur un hébergement HTTPS gratuit (GitHub Pages, Netlify, Vercel…)
   ou servez-le depuis un PC du même réseau Wi-Fi.
2. Ouvrez l'URL dans Chrome Android → menu ⋮ → **« Installer l'application »** (ou bouton « Installer l'app » dans RépétiPro).
3. L'icône RépétiPro apparaît sur l'écran d'accueil ; l'app fonctionne ensuite **sans Internet**.

> Pendant le développement dans cet environnement, l'app est servie en **aperçu direct** (panneau de prévisualisation).

### Option B — Ordinateur (test local)
```bash
cd repetipro
python3 -m http.server 8765 --bind 0.0.0.0
# puis ouvrir http://localhost:8765
```
(Aucune étape de compilation : HTML/CSS/JS classiques. Node ≥ 18 requis uniquement pour les tests.)

---

## 2. Fonctionnalités réellement opérationnelles ✅

| Domaine | Implémenté et testé |
|---|---|
| Tableau de bord | Élèves actifs/archivés, encaissé du mois (réel), reste à recevoir (attendu), échéances du jour, retards + montant, paiements annulés séparés, prochaines échéances, derniers paiements. Tout est recalculé après chaque opération. |
| Élèves | Créer / modifier / rechercher (nom, classe, téléphone) / filtrer (cycle, statut, situation de paiement) / archiver (historique conservé) / supprimer (refusé s'il existe des paiements, double confirmation sinon). |
| Répétitions & périodes | Un élève → plusieurs répétitions → plusieurs périodes. Nouvelle période sans écraser les anciennes. Renouvellement manuel (fiche élève + écran Échéances) avec confirmation tarif + date. Suspendre / annuler / réactiver une période (annulée = conservée dans l'historique). |
| Échéances | **+1 mois calendaire** (31/01 → 28/02 ou 29/02 ; 31/03 → 30/04). Dates stockées en `AAAA-MM-JJ` locales (aucun décalage de fuseau). Statuts : à venir, aujourd'hui, en retard, partiel, partiel-en-retard, payée (uniquement si solde = 0), suspendue, annulée. |
| Paiements | Intégral, partiel, multi-versements, ancienne période. Confirmation avant validation, anti-double-envoi, surpaiement refusé. Annulation **documentée** (motif obligatoire) : le paiement et le reçu restent visibles « Annulé », le solde est recalculé ; correction = annuler puis ré-enregistrer. |
| Reçus | Générés **uniquement pour de l'argent encaissé**. N° unique `RP-AAAA-000001` (compteur persistant, jamais réutilisé, même après restauration). Instantané figé des montants/noms : les anciens reçus ne changent jamais. **PDF (A4 ou compact), PNG, aperçu, partage Android (Web Share), impression, recherche.** |
| Rapports | Mois au choix : encaissé réel, soldes à recevoir, retards, partiels, journalier, par élève, par moyen de paiement. Export **CSV** et **PDF**. Recettes encaissées ≠ montants attendus, partout. |
| Hors ligne | Tout (élèves, périodes, paiements, reçus, rapports) via IndexedDB + Service Worker. Badge En ligne / Hors ligne en temps réel. |
| Sauvegarde | Export JSON avec **somme de contrôle** ; restauration validée **avant** tout remplacement (une sauvegarde corrompue est rejetée, données intactes) ; identifiants préservés ; rapport de réussite. |
| Journal de synchro | Chaque mutation est journalisée (file d'opérations) ; compteur « en attente d'export » ; marquage manuel après export vérifié. |
| Rappels | J-3, jour J, J+délai configurable ; activables séparément ; anti-doublons (clés persistées) ; annulés automatiquement si la période devient payée/annulée/suspendue ; notification système si autorisée + rappel dans l'app à l'ouverture. |
| Paramètres | Nom d'activité, téléphone, coordonnées (imprimés sur les reçus), devise (FCFA par défaut), format des reçus, préférences de rappel, à propos. |

## 3. Limites connues (assumées, rien n'est simulé) ⚠️

1. **Pas d'APK native produite ici** : l'environnement de création n'a ni Flutter ni SDK Android/Gradle.
   La PWA couvre le besoin Android ; voir §6 pour générer une vraie APK en 10 minutes.
2. **Pas de synchronisation cloud automatique** : il n'existe pas de backend dans cette v1 (aucun serveur, aucune clé).
   La synchronisation = export/import de sauvegardes vérifiées (à déposer sur Google Drive, e-mail, WhatsApp…).
   Google Drive seul n'est pas une base de données multi-appareils : ne modifiez pas la même sauvegarde sur deux téléphones en parallèle.
   Piste v2 : Supabase (base + authentification) en réutilisant la file `syncops` déjà en place (identifiants stables, opérations horodatées, paiements jamais écrasés par une version plus ancienne).
3. **Notifications** : une PWA fermée ne peut pas garantir une alarme à heure exacte sur Android (économie de batterie).
   Les rappels s'affichent à l'ouverture de l'app (+ notification système si autorisée) ; en APK TWA, même limite sans code natif d'alarme.
4. **Stockage navigateur** : IndexedDB est persistant, mais « Effacer les données de navigation » ou désinstaller le navigateur supprime les données
   → exportez une sauvegarde régulièrement (recommandé : après chaque journée d'encaissements).
5. Mono-répétiteur, sans comptes ni mots de passe (volontaire pour la v1). Facturation mensuelle uniquement.
   PDF limité aux caractères Latin-1 (français OK) ; pas de logo image sur le PDF (en-tête typographique).

## 4. Schéma de données (IndexedDB `repetipro`, 7 magasins)

```
ELEVE        id, nomComplet, classe, cycle(primaire|college|lycee), etablissement, parent,
             telephone, matieres, tarifMensuel(entier|null), dateDebut, notes,
             statut(actif|archive), createdAt, updatedAt
REPETITION   id, eleveId→ELEVE, matière, dateDebut, tarifConvenu(entier), frequence(mensuelle),
             statut, notes, createdAt, updatedAt
PERIODE      id, repetitionId→REPETITION, dateDebut, dateEcheance(=debut+1 mois calendaire),
             montantDu(entier), statutManuel(active|suspendue|annulee), createdAt, updatedAt
             → statut affiché = calculé (date du jour, solde) — voir logic.js:statutPeriode
PAIEMENT     id, periodeId→PERIODE, montant(entier>0), datePaiement(ISO), moyenPaiement
             (especes|mobile_money|virement|autre), reference, note, statut(valide|annule),
             motifAnnulation, createdAt
             → solde = montantDu − Σ paiements valides (entiers FCFA, jamais de flottants)
RECU         id, paiementId→PAIEMENT, numero(RP-AAAA-000001, unique), dateGeneration,
             statut(valide|annule), snapshot{élève, classe, matière, période, montants, activité…}
             → PNG/PDF régénérés à la demande depuis l'instantané (aucun fichier à perdre)
SYNCOPS      id, typeEntite, entiteId, operation, statut(en_attente|synchronise_manuel),
             tentatives, derniereErreur, updatedAt
META         settings{activite, telephone, coordonnees, devise, formatRecu, notif…},
             compteurRecu (séquence jamais réutilisée)
```

## 5. Sauvegarde & restauration — procédure

**Exporter** : Plus → Sauvegarde & synchronisation → « Exporter une sauvegarde ». Un fichier
`repetipro-sauvegarde-AAAA-MM-JJ.json` est téléchargé : déposez-le sur Google Drive (recommandé) ou envoyez-le-vous par e-mail.

**Restaurer** : même écran → « Restaurer une sauvegarde » → choisissez le fichier.
L'app vérifie d'abord la structure et la somme de contrôle ; si tout est valide, elle demande confirmation,
**puis seulement** remplace les données locales (identifiants et numéros de reçu préservés).

## 6. Produire une APK Android (à faire sur un poste avec accès Internet)

La PWA est déjà installable ; pour un fichier `.apk` distribuable :

1. Hébergez le dossier en HTTPS (ex. GitHub Pages).
2. Allez sur **pwabuilder.com**, saisissez l'URL → « Package for stores » → Android → téléchargez l'APK
   (alternative en ligne de commande : `npx @bubblewrap/cli init --manifest <url>/manifest.webmanifest && npx @bubblewrap/cli build`).
3. Installez l'APK sur le téléphone (sources inconnues à autoriser si installation directe).

⚠️ L'APK-TWA partage le stockage du navigateur d'origine : **exportez une sauvegarde depuis la PWA, puis importez-la dans l'APK** après installation.

## 7. Tests exécutés (résultats réels — 46 vérifications, 0 échec)

```bash
node tests/test-logic.mjs       # 28/28 — échéances (15/01, 31/01, 31/03, 22/10, bissextile),
                                # soldes/partiels, statuts, PDF généré, sauvegarde, rappels
python3 tests/test-e2e.py       # 13/13 — vrai navigateur Chromium : élève → période 31/01→28/02 →
                                # 2 versements → reçus 000001/000002 → exports PDF+PNG →
                                # création HORS LIGNE → redémarrage navigateur → persistance
python3 tests/test-restauration.py # 5/5 — export → effacement → restauration → sauvegarde corrompue rejetée
```
Le PDF produit a en outre été relu par un lecteur PDF réel (pypdf) : texte et accents corrects.
Captures : `tests/capture-dashboard.png`, `tests/capture-eleves.png` ; exemple : `tests/exemple-recu.pdf`.

**Restant à tester manuellement sur votre téléphone** : installation PWA + redémarrage du téléphone,
partage d'un reçu vers WhatsApp, impression, comportement des notifications avec l'économie de batterie de votre modèle.

## 8. Architecture des fichiers

```
repetipro/
├── index.html            écrans A→K (structure)
├── styles.css            charte bleu marine / turquoise, navigation basse, impression
├── logic.js              métier pur testable : dates, argent, statuts, reçus, PDF, sauvegarde
├── app.js                application : IndexedDB, écrans, paiements, rapports, rappels, synchro
├── sw.js                 Service Worker (cache hors ligne)
├── manifest.webmanifest  installation Android
├── icon.svg              logo typographique RP
└── tests/                suites ci-dessus + captures + exemple de reçu PDF
```
