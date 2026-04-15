import reflex as rx


class AstreinteEntry(rx.Base):
    period: str = ""
    slot_matin: str = ""
    slot_soir: str = ""


class PlanningEntry(rx.Base):
    tech_name: str = ""
    horaire: str = ""
    telework_days: str = ""
    bendoc_pause: str = ""


class PlanningRow(rx.Base):
    technician_name: str = ""
    horaire: str = ""
    telework_days: str = ""
    bendoc_pause: str = ""


class TechPresence(rx.Base):
    nom: str = ""
    initials: str = ""
    color: str = ""
    status: str = ""  # "present" | "tt" | "absent" | "repos"


class TicketTrend(rx.Base):
    week: str = ""
    crees: int = 0
    resolus: int = 0


class QuickLink(rx.Base):
    id: str = ""
    nom: str = ""
    url: str = ""


class LogEntry(rx.Base):
    timestamp: str = ""
    user_nom: str = ""
    action: str = ""
    entity: str = ""
    detail: str = ""


class PermRow(rx.Base):
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


class FeedbackItem(rx.Base):
    id: str = ""
    titre: str = ""
    description: str = ""
    type: str = ""
    statut: str = ""
    priorite: str = ""
    auteur_nom: str = ""
    date_creation: str = ""
    votes_count: int = 0


class ActualiteItem(rx.Base):
    id: str = ""
    titre: str = ""
    contenu: str = ""
    type: str = ""
    epingle: bool = False
    auteur_nom: str = ""
    date_creation: str = ""


class DocumentItem(rx.Base):
    id: str = ""
    type: str = ""
    nom_original: str = ""
    url: str = ""
    categorie: str = ""
    sous_categorie: str = ""
    description: str = ""


class GabaritItem(rx.Base):
    id: str = ""
    titre: str = ""
    categorie: str = ""
    contenu: str = ""
    date_creation: str = ""
    auteur_nom: str = ""


class DocGroup(rx.Base):
    name: str = ""
    docs: list[DocumentItem] = []


class TicketItem(rx.Base):
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


class TechnicienItem(rx.Base):
    id: str = ""
    nom: str = ""
    matricule: str = ""
    email: str = ""
    color: str = ""
    active: bool = True


class EscaladeEntry(rx.Base):
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


class QueteItem(rx.Base):
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


class LeaderboardEntry(rx.Base):
    user_id: str = ""
    nom: str = ""
    color: str = ""
    total_xp: int = 0
    level: int = 1
    rank: str = "E"
    quetes_validees: int = 0
    position: int = 1


class AmeliorationItem(rx.Base):
    id: str = ""
    titre: str = ""
    description: str = ""
    categorie: str = ""   # Process / UX / Technique / Formation / Autre
    priorite: str = ""    # Basse / Normale / Haute / Critique
    statut: str = ""      # Ouvert / En cours / Résolu / Fermé
    auteur_nom: str = ""
    date_creation: str = ""


class ProcSuiviRow(rx.Base):
    perimetre: str = ""
    typologie: str = ""
    categorie_fresh: str = ""
    has_procedure: bool = False
    procedure_source: str = ""   # "Intégrée" | "Personnalisée" | ""


class PendingValidation(rx.Base):
    quete_id: str = ""
    quete_titre: str = ""
    quete_icone: str = ""
    xp: int = 0
    user_id: str = ""
    user_nom: str = ""
