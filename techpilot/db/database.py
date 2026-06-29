import os
import copy
from pymongo import MongoClient
from dotenv import load_dotenv
from techpilot.gabarits_data import GABARIT_CATEGORIES_DEFAULT

load_dotenv()

DEFAULT_DOCUMENTS = [
    {"id": "doc-001", "type": "lien", "nom_original": "Citrix - Fermeture / Reset session distante",
     "url": "https://docs.google.com/document/d/1_SdHCuP9agpmzTWjQRuuAPhXJhdg-kErXM8T7YsIHUY/edit?tab=t.0",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-002", "type": "lien", "nom_original": "N1 - Freshdesk - Processus de relance",
     "url": "https://docs.google.com/document/d/1_-dcN7IsTuhJZ9VOOdJF-7WzRdgewBJi/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-003", "type": "lien", "nom_original": "N1 - Looker - Demande d'accès à un Looker",
     "url": "https://docs.google.com/document/d/1AyZ-r9ZS8harLKOqKeXCpqOBAG-xNdDM/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-004", "type": "lien", "nom_original": "Fiche N1 Pixid",
     "url": "https://docs.google.com/spreadsheets/d/1y3Ljh1qedy7yEwS_6zgBLwnNvRE2heqh/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-005", "type": "lien", "nom_original": "N1 - Chrome - Générer un fichier HAR",
     "url": "https://docs.google.com/document/d/1JIufStysp2WzoZNajjPq-xlhps2JJKHiOKAjGOUjBaA/edit?tab=t.0",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-006", "type": "lien", "nom_original": "Fiche N1 Looker Studio",
     "url": "https://docs.google.com/spreadsheets/d/1BwAUYZYoaqVsRdVtTyx0-Lh1yaz7TOq3/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-007", "type": "lien", "nom_original": "N1 – Vol de poste de travail",
     "url": "https://docs.google.com/document/d/1NhUoBfOkmwoEx3f3Q1Eg1GxNFFAMPX2E/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Sécurité", "description": ""},
    {"id": "doc-008", "type": "lien", "nom_original": "N1 – Keeper – Prise en charge et résolutions des sollicitations",
     "url": "https://docs.google.com/document/d/1nMzX9ACO66Cc04fwsajNsf0RnkkVnMzd/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Sécurité", "description": ""},
    {"id": "doc-009", "type": "lien", "nom_original": "Fiche N1 Keeper",
     "url": "https://docs.google.com/spreadsheets/d/1bnPx6l4FU-JufS8IWx76VFItLn4dlOV7/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-010", "type": "lien", "nom_original": "Fiche N1 ancien portail",
     "url": "https://docs.google.com/spreadsheets/d/1SkJzphx_FeJQ7GvLxY6pZllyh6LeYCUG/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-011", "type": "lien", "nom_original": "N1 - Google Meet – prise en charge des incidents d'accès et d'ouverture",
     "url": "https://docs.google.com/document/d/1N-99E9ej65PX40jhS3s41KEev_WrF5jx/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-012", "type": "lien", "nom_original": "Fiche N1 CPU",
     "url": "https://docs.google.com/spreadsheets/d/1uwyNxeuOTNvy6tVsiFzBOB7TY6uwyR94/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-013", "type": "lien", "nom_original": "N1 - AD - Modifier le mdp d'un compte Phone Océan",
     "url": "https://docs.google.com/document/d/1ptjfRIfiMpjgKbYw-Y-cB5JEAAxjoG0s/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Poste de travail et périphériques", "description": ""},
    {"id": "doc-014", "type": "lien", "nom_original": "N1 - Citrix – le bureau virtuel ne se lance pas",
     "url": "https://docs.google.com/document/d/1f-6cbjadbhUilw07XjnhXPSH-5EoDT8_/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-015", "type": "lien", "nom_original": "N1 - Incident d'impression - Diagnostic, résolution et escalade",
     "url": "https://docs.google.com/document/d/1NcpeuFi9RuzhOLxVmfcJKlgXrcrjfl00/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Poste de travail et périphériques", "description": ""},
    {"id": "doc-016", "type": "lien", "nom_original": "N1 – Identifier l'entité et le poste de l'utilisateur",
     "url": "https://docs.google.com/document/d/1T4-BUTs4zS1I_K32r_pTPbtXjRdhlPyO/edit",
     "categorie": "Procédures", "sous_categorie": "Généralités", "description": ""},
    {"id": "doc-017", "type": "lien", "nom_original": "N1 – Ulteam – Connexion impossible",
     "url": "https://docs.google.com/document/d/1S4xXNd0scKTaNKvx69f0mBomSjLdfj3V/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-018", "type": "lien", "nom_original": "Demande de délégation de boite mail",
     "url": "https://docs.google.com/document/d/1LUFVWUv4uJhY_A5D50Mt4fCyC4UjgSdXZs1b6DnBYbI/edit?tab=t.0",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-019", "type": "lien", "nom_original": "Fiche N1 Numen",
     "url": "https://docs.google.com/spreadsheets/d/1JN3LChq4ofc0AOkC1UPnuUBdxhMkFM6h/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-020", "type": "lien", "nom_original": "N1 – Numen – sollicitations connues",
     "url": "https://docs.google.com/document/d/19Wc8sLT16fxPY1c10fodblBGCipiBDh8/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-021", "type": "lien", "nom_original": "Fiche N1 PLD",
     "url": "https://docs.google.com/spreadsheets/d/1k3Z8-lKtkZu-g31wTqqb3m6JAqBUJAD1/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-022", "type": "lien", "nom_original": "N1 - Citrix – une application ne se lance pas",
     "url": "https://docs.google.com/document/d/1rYJOHrExxAuyDDXXV_ijIcMX-uhZfWsl/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-023", "type": "lien", "nom_original": "N1 - Google Drive - Fichiers qui apparaissent ou disparaissent",
     "url": "https://docs.google.com/document/d/1L44nZbSHne9v72df5kMqJ5DdMgdUE7QW/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-024", "type": "lien", "nom_original": "N1 - Prise en charge des pannes matériels",
     "url": "https://docs.google.com/document/d/1I-jqmI5lZV0T9CJyfqfhcyFI2OIMHR6K/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Poste de travail et périphériques", "description": ""},
    {"id": "doc-025", "type": "lien", "nom_original": "N1 - Process Prévisoft",
     "url": "https://drive.google.com/drive/folders/1AtHbk8Ax8WPSldxx-Fwz4_MCwQKZDm__",
     "categorie": "Procédures", "sous_categorie": "Arbres & process N1", "description": ""},
    {"id": "doc-026", "type": "lien", "nom_original": "Fiche N1 Prévisoft",
     "url": "https://docs.google.com/spreadsheets/d/1sakMzsMze0JEzbt7_RJZl1CdYD9W26m8/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-027", "type": "lien", "nom_original": "Fiche N1 Myistra",
     "url": "https://docs.google.com/spreadsheets/d/1SnS2IWFmunROSPkNOM5pcpiL-j4k3iop/edit?gid=1951550828",
     "categorie": "Procédures", "sous_categorie": "Fiches Applications pour le N1", "description": ""},
    {"id": "doc-028", "type": "lien", "nom_original": "N1 - PMAD sur les postes des utilisateurs",
     "url": "https://docs.google.com/document/d/1tH_JyscAbv5kR616s86z8kfd7Dr0E_Jd/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Poste de travail et périphériques", "description": ""},
    {"id": "doc-029", "type": "lien", "nom_original": "N1 – Navigateur - Tests pour application SaaS",
     "url": "https://docs.google.com/document/d/1f1US5Nu5z4G22HO4ybl1vBXnJUUxXO7q/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-030", "type": "lien", "nom_original": "N1 – Citrix - Prise en charge des incidents",
     "url": "https://docs.google.com/document/d/1C87AxJjCX3Ol0TUZ1q74zXsE0C4Ehy5Q/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-031", "type": "lien", "nom_original": "Groupes droits par applications",
     "url": "https://docs.google.com/spreadsheets/d/11r-fTQ_UH1ZumMJOkxtlZtGXFo3_gLKV/edit?gid=1504803980",
     "categorie": "Groupes de droits", "sous_categorie": "", "description": ""},
    {"id": "doc-032", "type": "lien", "nom_original": "Bonne pratique utilisateur",
     "url": "https://docs.google.com/document/d/1_jqY216JM3EbKDFbM5_P_9ogAP-7Sf4N/edit",
     "categorie": "Général", "sous_categorie": "Généralités", "description": ""},
    {"id": "doc-033", "type": "lien", "nom_original": "N1 - Chrome - L'aperçu du PDF n'est pas disponible",
     "url": "https://docs.google.com/document/d/1opuqC3SZxYRRl2cwb4TpLV9nWmvieQtK5ZYo9elOKx0/edit?tab=t.0",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-034", "type": "lien", "nom_original": "Configuration Mobiles",
     "url": "https://docs.google.com/document/d/1oTNLKJ84x-6Km1lfynLBc87T2CzWMxSfIvo8BuyaACQ/edit?tab=t.0",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-035", "type": "lien", "nom_original": "[TELEPHONIE FIXE] Personnaliser les raccourcis de son téléphone fixe Blue sur MyIstra",
     "url": "https://docs.google.com/document/d/1S1R-Wsc7Hg7A98Q5FwZEi2UECyyB7h-z6BoFsCcwadM/edit?tab=t.0",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-036", "type": "lien", "nom_original": "N1 - Qualys - Utilisation pour les diagnostics",
     "url": "https://docs.google.com/document/d/1Po1zamQNjBVC7nkCvFrVGrgSQnNr5JWZ/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Poste de travail et périphériques", "description": ""},
    {"id": "doc-037", "type": "lien", "nom_original": "N1 - Routeur 4G-5G - Diagnostiquer",
     "url": "https://docs.google.com/document/d/1wKeDf9ZFPKZjIIwJ_3UkmLdmYxm4X4NL/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Réseau et internet", "description": ""},
    {"id": "doc-038", "type": "lien", "nom_original": "N1 – Centile - Supervision de ligne",
     "url": "https://docs.google.com/document/d/1nVwStkypKHIcpadaASi_4e5smeG1iCXn/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-039", "type": "lien", "nom_original": "N1 – Gmail - Attribution mail agence sur smartphone pro",
     "url": "https://docs.google.com/document/d/1ucAMxmffaD_p_mq8Q6hDMRshbVdWg7qV/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-040", "type": "lien", "nom_original": "N1 – Gmail - Délégation boite mail",
     "url": "https://docs.google.com/document/d/1D7ypT_5-QXpUxm7J6Wpuq2JaqvSq80Nm/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Outils collaboratifs", "description": ""},
    {"id": "doc-041", "type": "lien", "nom_original": "N1 - Téléphone IP - Ajout de raccourcis",
     "url": "https://docs.google.com/document/d/1Hhr-zCh4WCZsqZHzzINoP6m-5bpZfOZ0/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-042", "type": "lien", "nom_original": "N1 – Ulteam/Ergalis - Changement de domaine Ulteam",
     "url": "https://docs.google.com/document/d/1m7kv44Epp5H73SQWwewvSNogZgnVkSBC/edit",
     "categorie": "Procédures", "sous_categorie": "SI - AUTRES APPLICATIONS", "description": ""},
    {"id": "doc-043", "type": "lien", "nom_original": "N1 – Demande d'applications - Applications locales",
     "url": "https://docs.google.com/document/d/1Bihy1P3qH4PPpMH2Dl_viie89VOJsyXT/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Poste de travail et périphériques", "description": ""},
    {"id": "doc-044", "type": "lien", "nom_original": "N1 – Réseau – Prise en charge des incidents",
     "url": "https://docs.google.com/document/d/1C-TSHR7Zr9MGcW09oqhcN53LZ4RPN-dL/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Réseau et internet", "description": ""},
    {"id": "doc-045", "type": "lien", "nom_original": "Process validation des documents N1",
     "url": "https://drive.google.com/file/d/1cWTOtifQyzgBz2EQwWZLyKcZ3PZqgYVr/view?usp=sharing",
     "categorie": "Général", "sous_categorie": "Généralités", "description": ""},
    {"id": "doc-046", "type": "lien", "nom_original": "N1 - Téléphonie fixe - Message d'accueil/attente/hors horaire",
     "url": "https://docs.google.com/document/d/1y0lJrcvL6Jv75bf1R2-Qxc33s_pkpUXg/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-047", "type": "lien", "nom_original": "N1 - Smartphone - Configuration MMS/APN Bouygues Telecom sur Android",
     "url": "https://docs.google.com/document/d/1IqA_SbSO2Gh-gUXYstHDHgiMuuy30hFd/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-048", "type": "lien", "nom_original": "N1 - Téléphonie fixe - Modification du numéro d'affichage",
     "url": "https://docs.google.com/document/d/1p_ziSou0BRwVTNOsK_fuB3_iGEtciBOe/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
    {"id": "doc-049", "type": "lien", "nom_original": "N1 – Téléphonie mobile – Portail Bouygues",
     "url": "https://docs.google.com/document/d/1BEDQwT0C53o7PUVv1rTolgwzYbR6xVi1/edit",
     "categorie": "Procédures", "sous_categorie": "SI - Téléphonie", "description": ""},
]

DEFAULT_DB = {
    "technicians": [
        {"id": "1", "nom": "Bastian",  "matricule": "464", "active": True, "permissions": {}},
        {"id": "2", "nom": "Adrien",   "matricule": "529", "active": True, "permissions": {}},
        {"id": "3", "nom": "Mirgaël",  "matricule": "524", "active": True, "permissions": {}},
        {"id": "4", "nom": "Cédric",   "matricule": "518", "active": True, "permissions": {}},
        {"id": "5",  "nom": "Thaïs",    "matricule": "432", "active": False, "permissions": {}},
        {"id": "6",  "nom": "Alistair", "matricule": "556", "active": True,  "permissions": {}},
        {"id": "7",  "nom": "Tiphaine", "matricule": "590", "active": True,  "permissions": {}},
        {"id": "8",  "nom": "Sabrina",  "matricule": "",    "active": True,  "permissions": {}},
        {"id": "9",  "nom": "Benjamin", "matricule": "",    "active": True,  "permissions": {}},
        {"id": "10", "nom": "Axelle",   "matricule": "",    "active": True,  "permissions": {}},
    ],
    "planning": [],
    "astreintes": [
        {"id": "1", "period": "Mars 6 et 9",    "slot_matin": "Adrien",  "slot_soir": "Mirgaël"},
        {"id": "2", "period": "Avril 7 et 8",   "slot_matin": "Adrien",  "slot_soir": "Cédric"},
        {"id": "3", "period": "Mai 7 et 8",     "slot_matin": "Mirgaël", "slot_soir": "Cédric"},
        {"id": "4", "period": "Juin 8 et 9",    "slot_matin": "Cédric",  "slot_soir": "Mirgaël"},
        {"id": "5", "period": "Juillet 7 et 8", "slot_matin": "Mirgaël", "slot_soir": "Cédric"},
        {"id": "6", "period": "Août 6 et 7",    "slot_matin": "Adrien",  "slot_soir": "Cédric"},
    ],
    "escalation_matrix": [],
    "tickets": [],
    "documents": [],
    "actualites": [],
    "feedbacks": [],
    "quetes": [],
    "quetes_progress": [],
    "notifications": [],
    "audit_log": [],
    "manager_auth": {},
    "quick_notes": {},
    "quick_links": [],
    "changelog": [
        {
            "id": "cl-001",
            "version": "1.0",
            "date": "2026-03-01",
            "titre": "Lancement de TechPilot",
            "type": "feature",
            "items": [
                "Dashboard avec KPIs et widgets personnalisables",
                "Planning hebdomadaire (import Excel)",
                "Matrice d'escalade N1/N2/N3 — 401 entrées",
                "Gestion des tickets N1",
                "Page Techniciens",
                "Import Excel (planning + matrice)",
            ],
        },
        {
            "id": "cl-002",
            "version": "1.1",
            "date": "2026-03-15",
            "titre": "Documents, Gabarits & Actualités",
            "type": "feature",
            "items": [
                "Base documentaire avec recherche et filtres",
                "Gabarits par catégorie (kanban) avec copie presse-papiers",
                "Page Actualités (info / succès / avertissement / alerte)",
                "Widget Actualités sur le dashboard",
            ],
        },
        {
            "id": "cl-003",
            "version": "1.2",
            "date": "2026-03-28",
            "titre": "Quêtes, Feedbacks & Admin",
            "type": "feature",
            "items": [
                "Système de quêtes et gamification (XP, niveaux, rangs E→S)",
                "Leaderboard de l'équipe",
                "Page Feedbacks (bugs, suggestions, améliorations)",
                "Page Permissions (gestion des droits par technicien)",
                "Journal d'audit (toutes les actions tracées)",
            ],
        },
        {
            "id": "cl-004",
            "version": "1.3",
            "date": "2026-04-07",
            "titre": "Procédures N1, liaisons documents & profil",
            "type": "feature",
            "items": [
                "Procédures N1 éditables dans la matrice d'escalade",
                "Historique des versions de procédure avec restauration",
                "Liaison document/gabarit/URL sur chaque entrée matrice",
                "Tableau de suivi des procédures",
                "Page Profil utilisateur (changement de mot de passe)",
                "Notes rapides auto-sauvegardées (widget + fenêtre dédiée)",
                "Liens rapides personnalisables sur le dashboard",
            ],
        },
        {
            "id": "cl-005",
            "version": "1.4",
            "date": "2026-04-21",
            "titre": "Recherche globale, Stats & Changelog",
            "type": "feature",
            "items": [
                "Recherche globale Ctrl+K (tickets, matrice, documents, gabarits)",
                "Widget Stats techniciens sur le dashboard",
                "Widget Mises à jour (changelog) sur le dashboard",
                "Page Mode Opératoire imprimable (/modop)",
                "Formulaire création ticket redesigné (style Freshservice)",
            ],
        },
        {
            "id": "cl-006",
            "version": "1.5",
            "date": "2026-06-29",
            "titre": "Rédacteur de Procédures N1 + Migration Loop→Drive",
            "type": "feature",
            "items": [
                "Rédacteur de procédures N1 avec assistant Claude intégré",
                "Génération automatique via Claude (format structuré N1)",
                "Comparateur de doublons contre les 49 Google Docs existants",
                "Workflow de validation : Brouillon → En attente → Relecture N1/N2 → Publié",
                "Kanban privé « Migration Loop→Drive » (Idées / En cours / Réalisés)",
                "Import astreintes depuis Prévision planning ACTUAL 2026.xlsx",
                "Arrivée d'Axelle, départ de Thaïs",
            ],
        },
    ],
    "migration_tasks": [],
    "procedures_content": [],
    "formation_modules": [],
    "onboarding_steps": [
        {"id": "ob-01", "titre": "Création du compte Active Directory", "description": "Création login, ajout aux groupes de sécurité N1", "categorie": "Accès", "ordre": 0},
        {"id": "ob-02", "titre": "Accès VPN et poste de travail", "description": "Installation client VPN, test de connexion", "categorie": "Accès", "ordre": 1},
        {"id": "ob-03", "titre": "Accès Freshservice", "description": "Création du compte agent, présentation de l'interface", "categorie": "Outils", "ordre": 2},
        {"id": "ob-04", "titre": "Présentation de l'équipe et du process N1", "description": "Tour d'équipe, explication des rôles et escalades", "categorie": "Processus", "ordre": 3},
        {"id": "ob-05", "titre": "Formation outil Mayday", "description": "Prise en main de la base de connaissances Mayday", "categorie": "Outils", "ordre": 4},
        {"id": "ob-06", "titre": "Lecture de la matrice d'escalade", "description": "Parcourir les 401 entrées, comprendre les périmètres", "categorie": "Formation", "ordre": 5},
        {"id": "ob-07", "titre": "Accès aux gabarits de réponse", "description": "Utilisation des gabarits dans TechPilot et Freshservice", "categorie": "Outils", "ordre": 6},
        {"id": "ob-08", "titre": "Premier ticket supervisé", "description": "Traitement d'un ticket en binôme avec un référent", "categorie": "Processus", "ordre": 7},
    ],
    "onboarding_progress": [],
}

_client = None
_collection = None
_cache: dict | None = None


def init_db():
    global _client, _collection, _cache
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("[DB] Mode mémoire (MONGODB_URI absent)")
        _cache = copy.deepcopy(DEFAULT_DB)
        return
    _client = MongoClient(uri)
    _collection = _client["techpilot"]["techpilot_dbs"]
    doc = _collection.find_one({"_id": "main"})
    if not doc:
        _collection.insert_one({"_id": "main", **DEFAULT_DB})
        doc = _collection.find_one({"_id": "main"})
    _cache = {k: v for k, v in doc.items() if k != "_id"}

    # Ajoute les techniciens du DEFAULT_DB manquants dans la DB existante
    existing_ids   = {str(t.get("id")) for t in _cache.get("technicians", [])}
    existing_names = {str(t.get("nom", "")).lower() for t in _cache.get("technicians", [])}
    missing = [
        t for t in DEFAULT_DB["technicians"]
        if str(t.get("id")) not in existing_ids and str(t.get("nom", "")).lower() not in existing_names
    ]
    if missing:
        _cache.setdefault("technicians", []).extend(missing)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"technicians": _cache["technicians"]}},
        )
        print(f"[DB] Techniciens ajoutés : {[t['nom'] for t in missing]}")

    # Ajoute les entrées changelog manquantes
    existing_cl_ids = {str(e.get("id")) for e in _cache.get("changelog", [])}
    missing_cl = [e for e in DEFAULT_DB["changelog"] if str(e.get("id")) not in existing_cl_ids]
    if missing_cl:
        _cache.setdefault("changelog", []).extend(missing_cl)
        _cache["changelog"].sort(key=lambda e: e.get("date", ""), reverse=True)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"changelog": _cache["changelog"]}},
        )
        print(f"[DB] Changelog ajouté : {[e['titre'] for e in missing_cl]}")

    # Ajoute les étapes onboarding manquantes
    existing_ob_ids = {str(s.get("id")) for s in _cache.get("onboarding_steps", [])}
    missing_ob = [s for s in DEFAULT_DB["onboarding_steps"] if str(s.get("id")) not in existing_ob_ids]
    if missing_ob:
        _cache.setdefault("onboarding_steps", []).extend(missing_ob)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"onboarding_steps": _cache["onboarding_steps"]}},
        )
        print(f"[DB] Étapes onboarding ajoutées : {len(missing_ob)}")

    # Migration équipe : désactiver Thaïs (départ), Axelle déjà gérée par le sync ci-dessus
    _team_changed = False
    for t in _cache.get("technicians", []):
        if t.get("nom", "").lower() in ("thaïs", "thais") and t.get("active", True):
            t["active"] = False
            _team_changed = True
            print("[DB] Thaïs désactivée (départ)")
    if _team_changed and _collection is not None:
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"technicians": _cache["technicians"]}},
        )

    # Initialise les clés manquantes dans le document MongoDB existant
    _missing_keys = {
        k: DEFAULT_DB[k]
        for k in DEFAULT_DB
        if k not in _cache
    }
    if _missing_keys and _collection is not None:
        _cache.update(_missing_keys)
        _collection.update_one(
            {"_id": "main"},
            {"$set": _missing_keys},
        )
        print(f"[DB] Clés initialisées : {list(_missing_keys.keys())}")

    # Ajoute les documents par défaut manquants (vérification par URL)
    existing_doc_urls = {str(d.get("url")) for d in _cache.get("documents", [])}
    missing_docs = [d for d in DEFAULT_DOCUMENTS if d["url"] not in existing_doc_urls]
    if missing_docs:
        _cache.setdefault("documents", []).extend(missing_docs)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"documents": _cache["documents"]}},
        )
        print(f"[DB] Documents ajoutés : {len(missing_docs)}")

    # Migre les catégories gabarits si elles ont changé
    saved_cats = _cache.get("gabarit_categories")
    if saved_cats != GABARIT_CATEGORIES_DEFAULT:
        _cache["gabarit_categories"] = list(GABARIT_CATEGORIES_DEFAULT)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"gabarit_categories": _cache["gabarit_categories"]}},
        )
        print(f"[DB] Catégories gabarits mises à jour : {GABARIT_CATEGORIES_DEFAULT}")

    print(f"[DB] MongoDB connecté — {len(_cache.get('technicians', []))} techniciens")


def load_db() -> dict:
    if _cache is None:
        init_db()
    return _cache


def save_db(data: dict):
    global _cache
    _cache = data
    if _collection is not None:
        _collection.update_one(
            {"_id": "main"},
            {"$set": {k: v for k, v in data.items() if k != "_id"}},
            upsert=True,
        )
