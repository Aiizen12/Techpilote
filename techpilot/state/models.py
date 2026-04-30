from pydantic import BaseModel


class ChangelogEntry(BaseModel):
    id: str = ""
    version: str = ""
    date: str = ""
    titre: str = ""
    items: list[str] = []
    type: str = "feature"   # "feature" | "fix" | "amélioration"


class AstreinteEntry(BaseModel):
    period: str = ""
    slot_matin: str = ""
    slot_soir: str = ""


class PlanningEntry(BaseModel):
    tech_name: str = ""
    horaire: str = ""
    telework_days: str = ""
    bendoc_pause: str = ""


class PlanningRow(BaseModel):
    technician_name: str = ""
    horaire: str = ""
    telework_days: str = ""
    bendoc_pause: str = ""


class TechPresence(BaseModel):
    nom: str = ""
    initials: str = ""
    color: str = ""
    status: str = ""  # "present" | "tt" | "absent" | "repos"


class TicketTrend(BaseModel):
    week: str = ""
    crees: int = 0
    resolus: int = 0


class QuickLink(BaseModel):
    id: str = ""
    nom: str = ""
    url: str = ""


class LogEntry(BaseModel):
    timestamp: str = ""
    user_nom: str = ""
    action: str = ""
    entity: str = ""
    detail: str = ""


class PermRow(BaseModel):
    id: str = ""
    nom: str = ""
    planning_edit: bool = False
    matrix_edit: bool = False
    technicians_edit: bool = False
    tickets_manage: bool = False
    import_excel: bool = False
    permissions_manage: bool = False
    escalade_proc_edit: bool = False
    doc_edit: bool = False


class FeedbackItem(BaseModel):
    id: str = ""
    titre: str = ""
    description: str = ""
    type: str = ""
    statut: str = ""
    priorite: str = ""
    auteur_nom: str = ""
    date_creation: str = ""
    votes_count: int = 0
    notes: str = ""


class ActualiteItem(BaseModel):
    id: str = ""
    titre: str = ""
    contenu: str = ""
    type: str = ""
    epingle: bool = False
    auteur_nom: str = ""
    date_creation: str = ""


class DocumentItem(BaseModel):
    id: str = ""
    type: str = ""
    nom_original: str = ""
    url: str = ""
    categorie: str = ""
    sous_categorie: str = ""
    description: str = ""


class GabaritItem(BaseModel):
    id: str = ""
    titre: str = ""
    categorie: str = ""
    contenu: str = ""
    date_creation: str = ""
    auteur_nom: str = ""
    is_custom: bool = False


class GabaritColumn(BaseModel):
    category: str = ""
    items: list[GabaritItem] = []


class DocGroup(BaseModel):
    name: str = ""
    docs: list[DocumentItem] = []


class MatrixSuggestion(BaseModel):
    key: str = ""
    perimetre: str = ""
    typologie: str = ""
    interlocuteur: str = ""
    traitement_n2n3: str = ""
    wp_n2: str = ""


class TicketItem(BaseModel):
    id: str = ""
    titre: str = ""
    ticket_pere: str = ""
    description: str = ""
    impact: str = ""
    perimetre: str = ""
    technicien_id: str = ""
    technicien_nom: str = ""
    etat: str = ""
    notes: str = ""
    date_creation: str = ""
    escalade_interlocuteur: str = ""
    escalade_n2: str = ""
    escalade_wp_n2: str = ""
    escalade_perimetre: str = ""
    escalade_typologie: str = ""


class TechnicienItem(BaseModel):
    id: str = ""
    nom: str = ""
    matricule: str = ""
    email: str = ""
    color: str = ""
    active: bool = True


class EscaladeEntry(BaseModel):
    perimetre: str = ""
    typologie: str = ""
    categorie_fresh: str = ""
    traitement_n1: str = ""
    wp: str = ""
    interlocuteur: str = ""
    traitement_n2n3: str = ""
    wp_n2: str = ""
    referents: str = ""
    conditions_escalade: str = ""
    notes: str = ""
    procedure_n1: list[str] = []
    doc_name: str = ""
    doc_url: str = ""


class QueteItem(BaseModel):
    id: str = ""
    titre: str = ""
    description: str = ""
    type: str = ""
    categorie: str = ""
    xp: int = 0
    objectif: int = 1
    unite: str = ""
    difficulte: str = "E"
    icone: str = "🎯"
    # Progression aplatie
    prog_progres: int = 0
    prog_statut: str = "en_cours"
    has_prog: bool = False


class LeaderboardEntry(BaseModel):
    user_id: str = ""
    nom: str = ""
    color: str = ""
    total_xp: int = 0
    level: int = 1
    rank: str = "E"
    quetes_validees: int = 0
    position: int = 1


class AmeliorationItem(BaseModel):
    id: str = ""
    titre: str = ""
    description: str = ""
    categorie: str = ""   # Process / UX / Technique / Formation / Autre
    priorite: str = ""    # Basse / Normale / Haute / Critique
    statut: str = ""      # Ouvert / En cours / Résolu / Fermé
    auteur_nom: str = ""
    date_creation: str = ""


class ProcSuiviRow(BaseModel):
    perimetre: str = ""
    typologie: str = ""
    categorie_fresh: str = ""
    has_procedure: bool = False
    procedure_source: str = ""   # "Intégrée" | "Personnalisée" | "Document" | ""
    doc_name: str = ""
    doc_url: str = ""


class PendingValidation(BaseModel):
    quete_id: str = ""
    quete_titre: str = ""
    quete_icone: str = ""
    xp: int = 0
    user_id: str = ""
    user_nom: str = ""


class DocPickerItem(BaseModel):
    id: str = ""
    nom: str = ""
    url: str = ""


class GlobalSearchResult(BaseModel):
    type: str = ""       # "ticket" | "matrice" | "document" | "gabarit"
    title: str = ""
    subtitle: str = ""
    href: str = ""
    key: str = ""        # id ou clé unique
    extra: str = ""      # contenu gabarit pour copie


class TechStatItem(BaseModel):
    nom: str = ""
    color: str = ""
    total: int = 0
    en_cours: int = 0
    resolus: int = 0
    escalades: int = 0


class ProcVersionItem(BaseModel):
    version: int = 0
    steps: list[str] = []
    date: str = ""
    auteur: str = ""


class AutoMatchProposal(BaseModel):
    doc_id: str = ""
    doc_name: str = ""
    doc_url: str = ""
    perimetre: str = ""
    typologie: str = ""
    score: int = 0


class FormationModule(BaseModel):
    id: str = ""
    titre: str = ""
    categorie: str = ""
    description: str = ""
    contenu: str = ""
    difficulte: str = "Débutant"
    auteur_nom: str = ""
    date_creation: str = ""
    lu_count: int = 0


class OnboardingStep(BaseModel):
    id: str = ""
    titre: str = ""
    description: str = ""
    categorie: str = "Général"
    ordre: int = 0


class OnboardingTechProgress(BaseModel):
    tech_id: str = ""
    tech_nom: str = ""
    color: str = ""
    steps_done: list[str] = []
    date_debut: str = ""
    assigned: bool = False
