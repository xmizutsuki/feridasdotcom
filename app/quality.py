"""Experimental, nonvalidated photographic quality metrics.

Thresholds are engineering heuristics, NOT clinical calibration or assurance of
diagnostic suitability. No lesion detection, segmentation or area inference.
"""
from dataclasses import dataclass
from io import BytesIO
from PIL import Image, ImageFilter, ImageStat
from pydantic import BaseModel, Field

MIN_LONG_EDGE = 640
LOW_LUMA = 45.0
HIGH_LUMA = 215.0
MIN_LUMA_SPREAD = 18.0
MIN_EDGE_VARIANCE = 35.0

class QualityReport(BaseModel):
    version: str = "heuristic-v1"
    width: int
    height: int
    brightness_mean: float = Field(ge=0, le=255)
    brightness_std: float = Field(ge=0)
    edge_variance: float = Field(ge=0)
    warnings: list[str]
    recapture_suggested: bool
    quantitative_measurement_allowed: bool = False
    clinical_validation: bool = False

def inspect_quality(jpeg: bytes) -> QualityReport:
    with Image.open(BytesIO(jpeg)) as original:
        width, height = original.size
        gray = original.convert("L")
        gray.thumbnail((640, 640))
        stats = ImageStat.Stat(gray)
        mean, std = stats.mean[0], stats.stddev[0]
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stats = ImageStat.Stat(edges)
        edge_var = edge_stats.var[0]
    warnings = []
    if max(width, height) < MIN_LONG_EDGE:
        warnings.append("Resolução limitada: aproxime a câmera sem cortar a lesão.")
    if mean < LOW_LUMA:
        warnings.append("Imagem escura: melhore a iluminação uniforme.")
    if mean > HIGH_LUMA:
        warnings.append("Imagem muito clara: evite reflexos e superexposição.")
    if std < MIN_LUMA_SPREAD:
        warnings.append("Baixo contraste: tente iluminação e enquadramento diferentes.")
    if edge_var < MIN_EDGE_VARIANCE:
        warnings.append("Poucos detalhes detectáveis: confira foco e estabilidade da câmera.")
    return QualityReport(
        width=width, height=height, brightness_mean=round(mean, 2),
        brightness_std=round(std, 2), edge_variance=round(edge_var, 2),
        warnings=warnings, recapture_suggested=bool(warnings),
    )
