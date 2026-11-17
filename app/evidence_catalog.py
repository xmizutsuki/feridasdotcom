"""Official source CATALOG metadata, not reproduced copyrighted guidelines.

Source presence does not mean any clinical passage or recommendation is verified.
URLs were checked against publishers' public pages at implementation.
"""
from typing import Final
CATALOG: Final[list[dict]] = [
    {
        "id":"iwgdf-2023-guidelines",
        "title":"Guidelines on the prevention and management of diabetes-related foot disease (2023)",
        "issuer":"IWGDF",
        "edition":"2023",
        "url":"https://iwgdfguidelines.org/guidelines-2023/",
        "scope":["diabetic_foot"],
        "verification_status":"publisher_page_identified",
    },
    {
        "id":"iwgdf-2023-wound-healing",
        "title":"Wound healing interventions guideline (2023 update)",
        "issuer":"IWGDF",
        "edition":"2023",
        "url":"https://iwgdfguidelines.org/wound-healing-2023/",
        "scope":["diabetic_foot","wound_healing"],
        "verification_status":"publisher_page_identified",
    },
    {
        "id":"sobest-library",
        "title":"Biblioteca científica SOBEST",
        "issuer":"SOBEST",
        "edition":"catálogo",
        "url":"https://sobest.com.br/biblioteca/",
        "scope":["wounds","stomatherapy"],
        "verification_status":"publisher_page_identified",
    },
]
