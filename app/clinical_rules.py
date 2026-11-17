"""Conservative warning prompts, not diagnosis or validated emergency screening.

Only explicit True responses trigger these flags. A negative or missing answer
does not indicate absence of risk. Rules have no autonomous treatment outputs.
"""
from .clinical_schemas import ClinicalHistoryIn

RULE_VERSION = "history-warnings-v1"

def generate_history_warnings(data: ClinicalHistoryIn) -> list[dict]:
    warnings = []
    def add(code: str, priority: str, text: str, fields: list[str]):
        warnings.append({"code": code, "priority": priority, "message": text,
                         "triggered_by": fields, "rule_version": RULE_VERSION})
    if data.rapidly_worsening is True:
        add("rapid_deterioration", "urgent_review",
            "Piora rápida relatada. Solicitar avaliação clínica presencial urgente; não utilizar este sistema para excluir emergências.",
            ["rapidly_worsening"])
    if data.fever_reported is True and (data.spreading_redness is True or data.purulent_drainage_reported is True):
        add("systemic_local_warning", "urgent_review",
            "Febre associada a alteração local relatada. Avaliação presencial urgente indicada para investigar causas; não configura diagnóstico por si só.",
            ["fever_reported", "spreading_redness" if data.spreading_redness is True else "purulent_drainage_reported"])
    if data.perfusion_exam == "concern_reported":
        add("perfusion_concern", "urgent_review",
            "Possível alteração de perfusão relatada. Solicitar avaliação clínica e vascular presencial, com prioridade conforme gravidade.",
            ["perfusion_exam"])
    if data.pain_worsening is True:
        add("pain_worsening", "review",
            "Piora da dor relatada. Reavaliar presencialmente a causa e possíveis sinais de deterioração.",
            ["pain_worsening"])
    if data.spreading_redness is True or data.purulent_drainage_reported is True:
        add("local_deterioration", "review",
            "Alteração local relatada: considerar avaliação clínica presencial de possível infecção ou outras causas.",
            [k for k in ("spreading_redness","purulent_drainage_reported") if getattr(data,k) is True])
    return warnings
