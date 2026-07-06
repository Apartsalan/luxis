# V2: strip eerst geciteerde AV-blokken (art. 9.3/20.4), label dan op de EIGEN tekst.
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open(sys.argv[1], encoding="utf-8"))

# Geciteerd voorwaarden-blok: vanaf "9.3 Indien Cliënt..." of "20.4 Indien een dossier..."
# tot einde alinea. Ook de losse citaat-varianten ("Indien Cliënt een incasso-opdracht intrekt...").
QUOTE_BLOCKS = [
    re.compile(r"9\.3[^\n]*Indien Cliënt.*?in rekening te brengen\.?", re.S | re.I),
    re.compile(r"Indien Cliënt een incasso-opdracht intrekt.*?in rekening te brengen\.?", re.S | re.I),
    re.compile(r"20\.4[^\n]*Indien een dossier.*?gemaakte kosten\.?", re.S | re.I),
    re.compile(r"No Cure No Pay\nDe werkwijze.*?juridische fase\.?", re.S | re.I),
    re.compile(r"Disclaimer\nEen gerechtelijke procedure.*?wederpartij\.?", re.S | re.I),
]

def own_text(body):
    t = body
    for q in QUOTE_BLOCKS:
        t = q.sub(" ", t)
    return t

RULES = [
    ("vertegenwoordiging", r"3:61|niet bevoegd|onbevoegd|gerechtvaardigd vertrouwen|opgewekt vertrouwen|schijn van|handtekening.{0,30}vervalst"),
    ("ncnp_gerechtelijke_fase", r"no cure no pay|ncnp"),
    ("consumentenbescherming_b2b", r"herroeping|bedenktijd|reflex-?werking|14-?dagenbrief|consumentenovereenkomst|als zakelijke partij"),
    ("av_toepasselijkheid", r"terhandstelling|6:23[34]|voorwaarden (zijn )?(wél|wel|nooit|niet).{0,30}(ontvangen|ter hand|gesloten)|registratieformulier"),
    ("opschorting_tegenvordering", r"6:7[45]|opschort|schuldeisers?verzuim|tegenvordering|verrekeningsgrond|wanprestatie|ingebrekestelling"),
    ("reeds_betaald_verrekening", r"reeds (betaald|voldaan)|al betaald|gecrediteerd|creditfactuur|creditnota|verreken|deelbetaling|bankafschrift|betalingen? aan facturen"),
    ("verlenging_opzegging", r"stilzwijgend|verlengd|verlenging|opgezegd|opzegging|opzegtermijn|aangetekend"),
    ("kosten_rente_hoogte", r"incassokosten.{0,160}(hoog|toelichting)|staffel|Besluit vergoeding|hoogte van de (rente|kosten)|minimumbedrag|minimumtarief"),
    ("betalingsregeling_schikking", r"betalingsregeling|finale kwijting|tegenvoorstel|schikkingsvoorstel|voorstel tot afwikkeling|bereid .{0,30}€|voorstel .{0,20}€|€.{0,40}tegen finale"),
    ("derde_partij", r"uw advocaat|advocaat in deze|rechtsbijstand|verzekeraar|overgedragen aan uw|via uw advocaat|advocate"),
    ("klacht_dienstverlening", r"inspanningsverplichting|klacht|dienstverlening|geen resultaat|BOOS"),
    ("afwikkeling_intrekking", r"9\.3|20\.4|afgewikkeld|intrekt|ingetrokken|intrekken|eindafrekening|afwikkeling|afgerond|af te ronden|afwikkelen|beëindigd"),
    ("betwisting_ongemotiveerd", r"stelplicht|bewijslast|niet onderbouwd|onderbouwt u niet|laat na .{0,40}(bewijs|onderbouw)|geen inhoudelijk verweer|toont u .{0,25}niet aan|aan u om .{0,40}(bewijzen|aan te tonen|bewijzen)|gemotiveerd (aan te tonen|uiteen)|mist .{0,25}grondslag|zonder concrete onderbouwing|niet.{0,15}gestaafd|snijden geen hout|algemene verwijten"),
]

counts, assign = {}, {}
residual = []
for c in data:
    t = own_text(c["body"])
    label = "overig"
    for key, pat in RULES:
        if re.search(pat, t, re.IGNORECASE):
            label = key
            break
    # Vangnet: als de EIGEN tekst niets oplevert maar het origineel citeert 9.3/20.4,
    # dan is de mail zelf een afwikkelings-antwoord.
    if label == "overig" and re.search(r"9\.3|20\.4", c["body"]):
        label = "afwikkeling_intrekking"
    counts[label] = counts.get(label, 0) + 1
    assign.setdefault(label, []).append(c["id"])
    if label == "overig":
        residual.append(c)

print("=== V2 verdeling (102 kandidaten) ===")
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"{k:32s} {v}   {', '.join(assign[k][:6])}{'...' if v > 6 else ''}")

print(f"\n=== Restant 'overig': {len(residual)} ===")
for c in residual:
    print(f"--- {c['id']}: {c['body'][:200]}".replace("\n", " "))
