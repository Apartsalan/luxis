# Toekomst-repos — adopteren zodra de trigger zich voordoet

> **Besluit Arsalan 22-7-2026 (S237):** open-source-onderzoek gedaan (10 videotools +
> breder GitHub). Conclusie: architectuur klopt, weinig te vervangen. Wat NU moest is
> direct gedaan (native structured outputs). De rest staat hier, elk met een concrete
> TRIGGER. **Attendering-regel: raakt een sessie een van onderstaande triggers, dan
> meldt Claude dit bij Arsalan vóór er gebouwd wordt.** (Zie ook CLAUDE.md → References.)

| Trigger (het moment) | Dan adopteren | Waarom dan pas |
|---|---|---|
| **Agent-laag bouwen** (besluit: AI mag zelf handelingen uitvoeren; komt als Luxis zo goed als klaar is — besluit Arsalan 22-7) | [pydantic-ai](https://pypi.org/project/pydantic-ai/) (MIT, productie-stabiel) | Niet de eigen slapende `ai_agent/tools/`-laag afbouwen; de handlers hergebruiken als functies, pydantic-ai als agent-motor. |
| **Tweede bank of tweede kantoor** met bankimport | CAMT.053-parser (bijv. [bankstatementparser](https://pypi.org/project/bankstatementparser/)) i.p.v. per bank een CSV-parser schrijven | CAMT.053 is de SEPA-standaard; huidige Rabobank-CSV-parser is bewezen op 255 betalingen — niet aanraken zolang er één bank is. |
| **AI-volume ×10** (± >500 aanroepen/dag) of tweede klant met eigen AI-gebruik | [Langfuse](https://langfuse.com) **self-hosted** (MIT) | Eigen `ai_usage`-tabel volstaat op 55/dag; Langfuse-cloud = extra verwerker voor debiteur-PII → alleen self-host overwegen. |
| **Klant eist "geen cloud-AI"** (aanbesteding/DPIA) | [Ollama](https://ollama.com) + EU-VPS met GPU als apart aanbod | Nu kwaliteitsverlies (NL-juridische taal) én geen GPU; als verkoopargument pas bouwen wanneer een klant erom vraagt. |
| **RAG tóch nodig** (heroverweging AVG-besluit S169 — alleen na expliciet besluit) | **pgvector** in de bestaande Postgres, NOOIT een losse vector-DB (Qdrant e.d.) | Zelfde backups/RLS/tenant-isolatie; losse vector-DB is voor miljoenen vectoren, wij zouden er duizenden hebben. |
| **Gescande/foto-PDF's worden een echte stroom** (nu: vrijwel alles digitale tekst-PDF) | [Docling](https://www.docling.ai/) (MIT) — níét Marker (GPL + gewichten-licentie) | pymupdf4llm + Claude-native-PDF dekken digitale PDF's al. |
| **Mail-strippen faalt zichtbaar** (handtekening/citaat lekt in geleerde antwoorden) | [mail-parser-reply](https://pypi.org/project/mail-parser-reply) (NL-ondersteuning) voor het generieke deel van `clean_answer_body` | Eigen regexes werken + menselijke goedkeuring vangt missers; alleen vervangen bij bewezen falen. |

## Bewust afgewezen (niet opnieuw beoordelen zonder nieuwe feiten)
- **LiteLLM** — wij zijn bewust single-provider (AVG S159); SDK-retries volstaan.
- **Outlines / Chonkie / Crawl4AI / Qdrant / DSPy / Marker** — zie rapport in sessieverloop S237: lossen problemen op die Luxis niet heeft of bewust vermeden heeft.

## Vaste bouwregel (verankerd in CLAUDE.md)
Nieuwe businesslogica altijd in de **service-laag** (router dun), zodat de toekomstige
agent-laag elke functie direct als tool-handler kan aanroepen. Dat is de enige
"agent-compatibiliteit" die nu iets kost — en hij is gratis als je je aan het
bestaande modulepatroon houdt.
