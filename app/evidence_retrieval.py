"""Small, transparent local lexical retrieval; NO automatically generated medical advice."""
import re
import unicodedata
from sqlalchemy import select
from sqlalchemy.orm import Session
from .evidence_catalog import CATALOG
from .models import EvidencePassage
from .evidence_schemas import EvidencePassageOut, EvidenceMatch, EvidenceSearchResult

SOURCE_BY_ID = {row["id"]: row for row in CATALOG}
STOPWORDS = {"a", "as", "o", "os", "e", "de", "do", "da", "dos", "das", "em",
             "no", "na", "para", "com", "um", "uma", "is", "and", "of", "in", "to",
             "the", "for", "on", "are", "with", "or"}

def terms(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value.lower())
    stripped = "".join(c for c in normalized if not unicodedata.combining(c))
    return {t for t in re.findall(r"[a-z0-9]{2,}", stripped) if t not in STOPWORDS}

def retrieve(db: Session, query: str, limit: int = 5) -> EvidenceSearchResult:
    query_tokens = terms(query)
    passages = db.scalars(select(EvidencePassage)).all()
    ranked = []
    for passage in passages:
        source = SOURCE_BY_ID.get(passage.catalog_source_id)
        if source is None:
            continue
        content_tokens = terms(passage.excerpt + " " + " ".join(passage.topic_tags))
        overlap = len(query_tokens & content_tokens)
        if overlap == 0:
            continue
        ranked.append((
            overlap,
            passage.id,
            EvidenceMatch(
                passage=EvidencePassageOut.model_validate(passage),
                publisher_title=source["title"],
                publisher_url=source["url"],
                lexical_score=overlap,
            ),
        ))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return EvidenceSearchResult(query=query, matches=[entry[2] for entry in ranked[:limit]])
