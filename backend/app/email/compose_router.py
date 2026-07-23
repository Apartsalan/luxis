"""Email compose router — compose emails via connected provider (Outlook/Gmail).

Generates .eml files that open directly in Outlook desktop as new compose windows
with all content pre-filled (recipients, subject, body, attachments).

Endpoints:
- POST /api/email/compose/send          — Send email via provider (direct)
- POST /api/email/compose/draft         — Create draft in provider
- POST /api/email/compose/cases/{id}    — Generate .eml file for Outlook desktop
- POST /api/email/compose/cases/{id}/render-template — Preview template as HTML
"""

import base64
import logging
import re
import uuid
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case, CaseActivity, CaseFile
from app.collections.models import Claim
from app.database import get_db
from app.dependencies import get_current_user
from app.documents.docx_service import build_base_context
from app.documents.rente_bijlage import build_rente_bijlage
from app.email.attachment_models import EmailAttachment
from app.email.incasso_templates import render_incasso_email
from app.email.oauth_service import (
    get_email_account,
    get_provider,
    get_valid_access_token,
    imap_smtp_kwargs,
    resolve_office_channel,
)
from app.email.providers.base import OutgoingAttachment
from app.email.send_service import ensure_branded_body, write_outbound_log
from app.email.subject import build_email_subject
from app.email.sync_service import EMAIL_ATTACHMENTS_BASE
from app.shared.exceptions import BadRequestError, NotFoundError

# Simpele adres-vorm-check aan de serverkant (de voorkant valideert ook, maar een
# API-call kan dat omzeilen). Niet volledig RFC 5322 — vangt de reële typefouten.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# AUD124-06: templates die automatisch factuur-PDF's als bijlage krijgen
AUTO_ATTACH_INVOICE_TYPES = {
    "14_dagenbrief",
    "aanmaning",
    "sommatie",
    "sommatie_na_reactie",
    "sommatie_eerste_opgave",
    "sommatie_drukte",
    "tweede_sommatie",
    "sommatie_laatste_voor_fai",
    "niet_voldaan_regeling",
    "faillissement_dreigbrief",
    "demand_for_payment_eerste",
    "demand_for_payment_uitgebreid",
    "demand_for_payment_laatste",
    "demand_for_payment_fai",
}

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email/compose", tags=["email-compose"])

# Upload storage base path (must match cases/files_service.py)
UPLOADS_BASE = Path("/app/uploads")

# Attachment limits
MAX_ATTACHMENT_SIZE = 3 * 1024 * 1024  # 3 MB per bijlage (Graph base64-limiet ~4MB/stuk)
# S232 (wens Arsalan): GEEN limiet meer op het AANTAL bijlagen. Wel een grens op de
# TOTALE mailgrootte — die is de echte beperking: de provider stopt alle bijlagen
# base64-gecodeerd in één verzendrequest. 25 MB dekt normale dossier-mails ruim en
# blijft onder de gangbare mailbox-grens; grotere mails geven een duidelijke melding
# i.p.v. een cryptische provider-fout.
# ponytail: harde 25MB-grens; een echte upload-sessie-route (Graph large attachments)
# bouwen we pas als dit knelt.
MAX_TOTAL_ATTACHMENT_SIZE = 25 * 1024 * 1024
# S202 L4: bovengrens op de base64-STRING (vóór decoderen) die exact overeenkomt
# met MAX_ATTACHMENT_SIZE gedecodeerd — zodat het schema al weigert in plaats van
# eerst volledig te decoderen en pas daarna de gedecodeerde grootte te checken.
MAX_ATTACHMENT_B64_LEN = ((MAX_ATTACHMENT_SIZE + 2) // 3) * 4


def _assert_total_attachment_size(attachments: list[OutgoingAttachment]) -> None:
    """Bewaak de TOTALE bijlage-grootte over alle routes (S232).

    Vervangt de oude aantal-limiet: het aantal maakt de provider niet uit, de totale
    request-grootte wel. Route-onafhankelijk aangeroepen vlak vóór verzending, met de
    volledige lijst (dossierbestanden + inline uploads + doorgestuurde + rente-PDF).
    """
    total = sum(len(a.data) for a in attachments)
    if total > MAX_TOTAL_ATTACHMENT_SIZE:
        raise BadRequestError(
            f"De bijlagen zijn samen te groot ({total // (1024 * 1024)} MB, "
            f"max {MAX_TOTAL_ATTACHMENT_SIZE // (1024 * 1024)} MB). "
            "Verstuur de grootste bestanden apart of via een download-link."
        )


# ── Schemas ──────────────────────────────────────────────────────────────────


class InlineAttachment(BaseModel):
    filename: str = Field(..., max_length=255)
    # S202 L4: cap op de RUWE base64-string, vóór decoderen — voorkomt dat een
    # oneindig grote payload eerst volledig gedecodeerd wordt en pas daarna op
    # grootte wordt afgewezen.
    data_base64: str = Field(..., max_length=MAX_ATTACHMENT_B64_LEN)
    content_type: str = Field(..., max_length=100)


class ComposeRequest(BaseModel):
    to: list[str] = Field(..., min_length=1, description="Ontvangers e-mailadressen")
    cc: list[str] | None = Field(default=None, description="CC e-mailadressen")
    bcc: list[str] | None = Field(default=None, description="BCC e-mailadressen")
    subject: str = Field(..., max_length=500, description="Onderwerp")
    body_html: str = Field(..., max_length=100000, description="HTML body")
    reply_to_message_id: str | None = Field(
        default=None, description="Provider message ID om op te antwoorden"
    )
    references_root: str | None = Field(
        default=None,
        description="Wortel van de gespreksdraad (References-root van het origineel)",
    )
    # Bijlagen — zonder deze velden liet /compose/send bijlagen stil vallen (S186).
    case_id: uuid.UUID | None = Field(
        default=None, description="Dossier voor het oplossen van dossierbijlagen"
    )
    case_file_ids: list[uuid.UUID] | None = None
    # S232: geen aantal-limiet meer; de totale grootte wordt vóór verzending bewaakt.
    inline_attachments: list[InlineAttachment] | None = None
    # Doorsturen: neem de bijlagen van de oorspronkelijke (gesyncte) mail mee.
    forward_from_email_id: uuid.UUID | None = Field(
        default=None, description="SyncedEmail-id om de bijlagen van door te sturen"
    )
    # True = de body draagt de huisstijl al (template of AI-concept) → niet
    # opnieuw aankleden. False (vrije mail/antwoord/doorsturen) → wel aankleden.
    already_branded: bool = False
    # S205: 'toch versturen'-override. False = de 14-dagenbrief-gate mag blokkeren;
    # True = de gebruiker heeft de blokkade-waarschuwing gezien en bewust doorgezet
    # (er wordt dan een onuitwisbaar spoor op het dossier gelegd).
    compliance_override: bool = False
    # S212-review: het gekozen incasso-sjabloon. Sleutel voor de renteoverzicht-
    # bijlage op dít (primaire) verzendpad — zelfde mechanisme als het .eml-pad.
    template_type: str | None = Field(default=None, max_length=50)
    # S232 — laat compose/send de pijplijn NIET doorschuiven. De voorkant zet dit op
    # true bij een AI-concept-review: dan regelt de aparte advance-after-send-call het
    # doorschuiven én de draft-status. Zonder deze guard zou een AI-concept waar de
    # gebruiker alsnog een sjabloon bij koos via BEIDE routes doorschuiven (dubbel).
    skip_pipeline_advance: bool = False

    @field_validator("to", "cc", "bcc")
    @classmethod
    def _validate_email_addresses(cls, v: list[str] | None) -> list[str] | None:
        for addr in v or []:
            if not _EMAIL_RE.match((addr or "").strip()):
                raise ValueError(f"Ongeldig e-mailadres: {addr!r}")
        return v


class CaseComposeRequest(BaseModel):
    recipient_email: str = Field(..., max_length=320)
    recipient_name: str | None = Field(default=None, max_length=200)
    cc: list[str] | None = None
    bcc: list[str] | None = None
    subject: str = Field(..., max_length=500)
    body: str = Field(default="", max_length=50000, description="Platte tekst body")
    body_html: str | None = Field(
        default=None, max_length=200000, description="HTML body (van template)"
    )
    case_file_ids: list[uuid.UUID] | None = None
    inline_attachments: list[InlineAttachment] | None = None
    # S224 — 'toch doorgaan'-override voor de 14-dagenbrief-gate op de .eml-route
    # (de vijfde verzenddeur; zelfde patroon als compose/send en documents/send).
    compliance_override: bool = False
    template_type: str | None = Field(
        default=None,
        max_length=50,
        description=(
            "DF122-07: bij 'sommatie' worden factuur-PDF's van claims "
            "automatisch als bijlage meegestuurd."
        ),
    )


class ComposeResponse(BaseModel):
    success: bool
    provider_message_id: str | None = None
    draft_id: str | None = None
    web_link: str | None = None
    message: str
    # S232 — of de verstuurde stap-brief het dossier heeft doorgeschoven, en waarheen
    # (voor de toast op de voorkant). Blijft False op alle niet-stap-routes.
    advanced: bool = False
    advanced_to_step: str | None = None


class RenderTemplateRequest(BaseModel):
    template_type: str = Field(..., max_length=50)
    # S244 — antwoord-flow: het geciteerde origineel komt onderaan de shell
    # (alleen gebruikt door "vrij_bericht"; andere sjablonen negeren dit).
    quoted_html: str | None = Field(default=None, max_length=200000)


class RenderTemplateResponse(BaseModel):
    supported: bool
    subject: str | None = None
    body_html: str | None = None


class AutoAttachmentsRequest(BaseModel):
    template_type: str | None = Field(default=None, max_length=50)
    recipient_email: str | None = Field(default=None, max_length=320)


class AutoAttachmentItem(BaseModel):
    label: str
    kind: str  # "rente" | "factuur" | "verzoekschrift"
    # S231: waar de frontend het bestand kan ópenen. Zonder deze twee velden was
    # het etiket een doodlopend label — de gebruiker zag dát er een bijlage
    # meeging maar kon hem niet inzien vóór verzending.
    # Server-gerenderde PDF → sjabloontype voor /documents/docx/.../render-pdf.
    template_type: str | None = None
    # Bestaand dossierbestand (factuur) → id voor /cases/{id}/files/{fid}/download.
    case_file_id: uuid.UUID | None = None


class AutoAttachmentsResponse(BaseModel):
    items: list[AutoAttachmentItem]


class InvoiceFileItem(BaseModel):
    """S233 — een factuur-PDF uit het dossier, als vooraf-aangevinkte bijlage."""

    id: uuid.UUID
    filename: str
    size: int


class InvoiceFilesResponse(BaseModel):
    items: list[InvoiceFileItem]


# ── Attachment resolver ──────────────────────────────────────────────────────


async def _resolve_attachments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    case_file_ids: list[uuid.UUID] | None,
    inline_attachments: list[InlineAttachment] | None,
) -> list[OutgoingAttachment]:
    """Load CaseFiles from disk + decode inline uploads into OutgoingAttachment list."""
    attachments: list[OutgoingAttachment] = []

    # CaseFiles from disk
    if case_file_ids:
        result = await db.execute(
            select(CaseFile).where(
                CaseFile.tenant_id == tenant_id,
                CaseFile.case_id == case_id,
                CaseFile.id.in_(case_file_ids),
                CaseFile.is_active.is_(True),
            )
        )
        case_files = result.scalars().all()

        for cf in case_files:
            file_path = UPLOADS_BASE / str(tenant_id) / str(case_id) / cf.stored_filename
            if not file_path.exists():
                logger.warning("CaseFile %s not found on disk: %s", cf.id, file_path)
                continue
            data = file_path.read_bytes()
            if len(data) > MAX_ATTACHMENT_SIZE:
                raise BadRequestError(
                    f"Bijlage '{cf.original_filename}' is te groot "
                    f"({len(data) // (1024 * 1024)} MB, max 3 MB)"
                )
            attachments.append(
                OutgoingAttachment(
                    filename=cf.original_filename,
                    data=data,
                    content_type=cf.content_type or "application/octet-stream",
                )
            )

    # Inline uploads (base64-encoded)
    if inline_attachments:
        for att in inline_attachments:
            try:
                data = base64.b64decode(att.data_base64)
            except Exception:
                raise BadRequestError(f"Ongeldige bijlage: '{att.filename}'")
            if len(data) > MAX_ATTACHMENT_SIZE:
                raise BadRequestError(
                    f"Bijlage '{att.filename}' is te groot "
                    f"({len(data) // (1024 * 1024)} MB, max 3 MB)"
                )
            attachments.append(
                OutgoingAttachment(
                    filename=att.filename,
                    data=data,
                    content_type=att.content_type or "application/octet-stream",
                )
            )

    return attachments


async def _load_forwarded_attachments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_id: uuid.UUID,
) -> list[OutgoingAttachment]:
    """Laad de bijlagen van een gesyncte mail van schijf, voor doorsturen.

    Ontbrekende bestanden of te grote bijlagen worden overgeslagen (loggen +
    doorgaan) — doorsturen mag niet stuklopen op één ontbrekende bijlage.
    """
    result = await db.execute(
        select(EmailAttachment).where(
            EmailAttachment.synced_email_id == email_id,
            EmailAttachment.tenant_id == tenant_id,
        )
    )
    out: list[OutgoingAttachment] = []
    for att in result.scalars().all():
        file_path = (
            EMAIL_ATTACHMENTS_BASE / str(tenant_id) / str(email_id) / att.stored_filename
        )
        if not file_path.exists():
            logger.warning("Doorstuur-bijlage niet op schijf: %s", file_path)
            continue
        data = file_path.read_bytes()
        if len(data) > MAX_ATTACHMENT_SIZE:
            logger.warning(
                "Doorstuur-bijlage '%s' te groot (%d MB) — overgeslagen",
                att.filename,
                len(data) // (1024 * 1024),
            )
            continue
        out.append(
            OutgoingAttachment(
                filename=att.filename,
                data=data,
                content_type=att.content_type or "application/octet-stream",
            )
        )
    return out


async def _derive_step_template_type(
    case: Case,
    recipient_emails: list[str],
) -> str | None:
    """Punt 1/25 — leid het brieftype af uit de huidige pijplijnstap.

    De AI-concept-route draagt geen sjabloontype mee (`ai_drafts` heeft geen
    stap-koppeling) → de server zag een 'gewone mail' en liet de wettelijke
    renteoverzicht-bijlage weg. Bij een VERSE dossier-mail AAN DE DEBITEUR zonder
    expliciet sjabloontype leiden we het brieftype af uit de huidige stap, zodat
    het renteoverzicht alsnog automatisch meegaat. Alleen als de ontvanger de
    debiteur van het dossier is (antwoord/doorsturen/mail-aan-cliënt → None).

    Levert uitsluitend het sjabloontype voor de bijlage-beslissing; het pad haakt
    hierop GEEN factuur-PDF's aan (bewuste keuze Arsalan, S218).
    """
    step = case.incasso_step
    if step is None or not step.template_type:
        return None
    debtor_email = ((case.opposing_party.email if case.opposing_party else None) or "").strip().lower()
    if not debtor_email:
        return None
    recipients = {(e or "").strip().lower() for e in recipient_emails}
    if debtor_email not in recipients:
        return None
    return step.template_type


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/send", response_model=ComposeResponse)
async def send_via_provider(
    data: ComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an email via the connected email provider (Outlook/BaseNet-IMAP)."""
    # S205 — wettelijke waarborg art. 6:96 lid 6 BW op het AI-concept/losse verzendpad
    # (de derde deur naast batch en follow-up). Alleen voor een VERSE case-mail (geen
    # antwoord/doorsturen) op een BIK-claimende sommatie-stap bij een consument. Zonder
    # override blokkeren met een herkenbare code zodat de voorkant de 'toch versturen'-
    # knop kan tonen; mét override gaat de mail door + onuitwisbaar spoor op het dossier.
    is_reply_or_forward = bool(data.reply_to_message_id or data.forward_from_email_id)
    if data.case_id and not is_reply_or_forward:
        from app.collections.compliance import (
            check_dagenbrief_gate_for_case,
            record_dagenbrief_override,
        )

        gate_reason = await check_dagenbrief_gate_for_case(db, user.tenant_id, data.case_id)
        if gate_reason is not None:
            if not data.compliance_override:
                raise HTTPException(
                    status_code=422,
                    detail={"code": "DAGENBRIEF_GATE", "message": gate_reason},
                )
            # Spoor vastleggen; commit gebeurt aan het eind van de request (get_db)
            # samen met de verzending — mislukt de send, dan rolt ook dit terug.
            await record_dagenbrief_override(
                db, user.tenant_id, data.case_id, user.id, gate_reason
            )

    # S220 (hoofdvondst N1) — afzender-vangrail: verstuur voortaan via het vaste
    # kantoorkanaal (incasso@), niet via de mailbox van wie klikt (patroon B13, zoals
    # batch/follow-up). Valt terug op het account van de gebruiker als er geen
    # kantoor-account verbonden is (geen regressie).
    # S231: het kantoorkanaal bepaalt nu ook het vervoer (Graph waar mogelijk,
    # anders BaseNet) — BaseNets relay staat op Microsofts blokkadelijst.
    account, send_from_address = await resolve_office_channel(db, user.tenant_id)
    if account is None:
        account = await get_email_account(db, user.id, user.tenant_id)
        send_from_address = None
    if not account:
        raise BadRequestError("Geen e-mailaccount verbonden. Ga naar Instellingen → E-mail.")

    provider = get_provider(account.provider)
    access_token = await get_valid_access_token(db, account)

    # Punt 1/25 — brieftype afleiden uit de huidige pijplijnstap als een VERSE
    # dossier-mail aan de debiteur geen sjabloontype meedraagt (AI-concept-route).
    # Alleen voor de renteoverzicht-bijlage; factuur-auto-attach blijft aan het
    # expliciete sjabloontype hangen (geen factuur-auto-attach op deze route).
    effective_template_type = data.template_type
    send_case: Case | None = None
    if data.case_id and not is_reply_or_forward:
        send_case = (
            await db.execute(
                select(Case).where(
                    Case.id == data.case_id, Case.tenant_id == user.tenant_id
                )
            )
        ).scalar_one_or_none()
        if effective_template_type is None and send_case is not None:
            effective_template_type = await _derive_step_template_type(send_case, data.to)

    # DF122-07 (S212): automatisch factuur-PDF's van claims bijvoegen bij een
    # sommatie-sjabloon — zelfde regel als het .eml-pad (compose_eml_from_case),
    # alleen voor een verse case-mail (geen antwoord/doorsturen).
    merged_case_file_ids: list[uuid.UUID] = list(data.case_file_ids or [])
    if (
        data.template_type in AUTO_ATTACH_INVOICE_TYPES
        and data.case_id
        and not is_reply_or_forward
    ):
        claims_result = await db.execute(
            select(Claim.invoice_file_id).where(
                Claim.case_id == data.case_id,
                Claim.tenant_id == user.tenant_id,
                Claim.is_active.is_(True),
                Claim.invoice_file_id.is_not(None),
            )
        )
        seen = set(merged_case_file_ids)
        for (inv_id,) in claims_result.all():
            if inv_id is not None and inv_id not in seen:
                merged_case_file_ids.append(inv_id)
                seen.add(inv_id)

    # Bijlagen oplossen (dossierbestanden + inline uploads). Vereist een dossier
    # voor de dossierbestanden; inline uploads kunnen ook zonder.
    resolved_attachments: list[OutgoingAttachment] = []
    if merged_case_file_ids or data.inline_attachments:
        if data.case_file_ids and not data.case_id:
            raise BadRequestError("Dossier ontbreekt voor de geselecteerde dossierbijlagen.")
        resolved_attachments = await _resolve_attachments(
            db,
            user.tenant_id,
            data.case_id,
            merged_case_file_ids or None,
            data.inline_attachments,
        )

    # Doorsturen: de bijlagen van de oorspronkelijke mail meesturen.
    if data.forward_from_email_id:
        resolved_attachments += await _load_forwarded_attachments(
            db, user.tenant_id, data.forward_from_email_id
        )

    # S212-review: renteoverzicht-PDF óók op deze primaire verzendknop ("Versturen").
    # Zelfde sleutel als het .eml-pad: het gekozen sjabloontype; alleen voor een verse
    # case-mail (geen antwoord/doorsturen). Bij een BV/NV/stichting → geen bijlage;
    # mislukt de send, dan rolt het opgeslagen renteoverzicht-document mee terug.
    if effective_template_type and data.case_id and not is_reply_or_forward:
        if send_case is not None:
            for rente_name, rente_bytes, _rente_type in await build_rente_bijlage(
                db,
                user.tenant_id,
                send_case,
                SimpleNamespace(template_type=effective_template_type),
                user.id,
            ):
                resolved_attachments.append(
                    OutgoingAttachment(
                        filename=rente_name,
                        data=rente_bytes,
                        content_type="application/pdf",
                    )
                )

    # S232: bewaak de TOTALE bijlage-grootte (geen aantal-limiet meer), met de
    # volledige lijst (dossierbestanden + inline + doorgestuurd + rente-PDF).
    _assert_total_attachment_size(resolved_attachments)

    # Huisstijl: vrije mail, beantwoorden en doorsturen krijgen dezelfde
    # sjabloon-opmaak (handtekening + logo + schuldhulpblok). Een via een
    # template of AI-concept opgestelde mail draagt de opmaak al → dan slaat de
    # voorkant `already_branded` aan en laten we 'm met rust.
    body_html = data.body_html
    if not data.already_branded:
        body_html = await ensure_branded_body(
            db,
            user.tenant_id,
            subject=data.subject,
            body_html=data.body_html,
            case_id=data.case_id,
            force=True,
        )

    from_name = (
        await db.execute(select(Tenant.name).where(Tenant.id == user.tenant_id))
    ).scalar() or ""

    try:
        message_id = await provider.send_message(
            access_token,
            to=data.to,
            subject=data.subject,
            body_html=body_html,
            cc=data.cc,
            bcc=data.bcc,
            reply_to_message_id=data.reply_to_message_id,
            references_root=data.references_root,
            attachments=resolved_attachments or None,
            from_name=from_name,
            from_address=send_from_address,
            **imap_smtp_kwargs(account),
        )
    except Exception as e:
        logger.error(f"Email verzenden mislukt via {account.provider}: {e}")
        raise BadRequestError(f"Verzenden mislukt: {e}")

    # S220 (hoofdvondst N1) — spoor vastleggen zodat de verstuurde mail terugvindbaar
    # is op de dossier-tijdlijn + in Correspondentie (voorheen legde dit pad NIETS vast).
    await write_outbound_log(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        to=data.to,
        subject=data.subject,
        body_html=body_html,
        account=account,
        provider_message_id=message_id,
        used_provider=True,
        status="sent",
        cc=data.cc,
        case_id=data.case_id,
        sender_name=from_name,
        template=data.template_type or "compose_send",
        has_attachments=bool(resolved_attachments),
        # S234 — draad-wortel: bij een antwoord de References-wortel (anders de
        # directe voorganger); zo groepeert de verstuurde mail op dezelfde draad
        # als het gesprek. Verse mail zonder antwoord-context → None, dan valt
        # write_outbound_log terug op het eigen message-id.
        provider_thread_id=data.references_root or data.reply_to_message_id,
        # S242 — bij 'Verzenden als' kantooradres het échte afzenderadres
        # vastleggen, niet de vervoerende mailbox.
        effective_from=send_from_address,
    )

    # S232 — doorschuiven na een verstuurde STAP-brief. Een verse dossier-mail aan de
    # debiteur met een EXPLICIET gekozen sjabloon dat bij de huidige pijplijnstap hoort,
    # schuift het dossier één stap door — dezelfde advance_to_step-regel als de AI-route.
    # Bewust op data.template_type (het gekozen sjabloon), NIET op het afgeleide
    # brieftype: de AI-concept-route draagt géén sjabloon en schuift al via
    # advance-after-send door → zo kan het nooit dubbel. Antwoord/doorsturen/vrij bericht
    # (is_reply_or_forward, of geen sjabloon) beweegt niets (huisregel P1). Herverzenden
    # van een eerdere brief matcht niet meer met de inmiddels verdere huidige stap → niets.
    advanced = False
    advanced_to_step: str | None = None
    if data.case_id and send_case is not None and send_case.incasso_step is not None:
        from app.incasso.service import (
            advance_after_step_send,
            should_advance_on_template_send,
        )

        if should_advance_on_template_send(
            data.template_type,
            is_reply_or_forward,
            send_case.incasso_step.template_type,
            skip_pipeline_advance=data.skip_pipeline_advance,
        ):
            advance_result = await advance_after_step_send(
                db,
                user.tenant_id,
                send_case,
                user.id,
                notes="Doorgeschoven na verzending sjabloon",
            )
            advanced = advance_result.get("advanced", False)
            advanced_to_step = advance_result.get("to_step_name")

    return ComposeResponse(
        success=True,
        provider_message_id=message_id,
        message="E-mail verzonden via " + account.provider,
        advanced=advanced,
        advanced_to_step=advanced_to_step,
    )


@router.post("/draft", response_model=ComposeResponse)
async def create_draft_via_provider(
    data: ComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft in the connected email provider."""
    account = await get_email_account(db, user.id, user.tenant_id)
    if not account:
        raise BadRequestError("Geen e-mailaccount verbonden. Ga naar Instellingen → E-mail.")

    provider = get_provider(account.provider)
    access_token = await get_valid_access_token(db, account)

    try:
        draft_id, web_link = await provider.create_draft(
            access_token,
            to=data.to,
            subject=data.subject,
            body_html=data.body_html,
            cc=data.cc,
        )
        return ComposeResponse(
            success=True,
            draft_id=draft_id,
            web_link=web_link,
            message="Concept aangemaakt in " + account.provider,
        )
    except Exception as e:
        logger.error(f"Draft aanmaken mislukt via {account.provider}: {e}")
        raise BadRequestError(f"Concept aanmaken mislukt: {e}")


@router.post("/cases/{case_id}")
async def compose_eml_from_case(
    case_id: uuid.UUID,
    data: CaseComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a .eml file that opens in Outlook desktop as a new email.

    The .eml contains recipients, subject, HTML body, and attachments.
    When opened on Windows, Outlook desktop shows it as a ready-to-send email.
    """
    # Verify case exists
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    # S224 (veegsessie, huisregel M3) — de .eml-route is de VIJFDE verzenddeur
    # (S205 dekte batch/follow-up/compose, S207 documents; deze bleef open): een
    # kant-en-klare sommatie die de gebruiker zelf via Outlook verstuurt valt
    # onder dezelfde wettelijke waarborg (art. 6:96 lid 6 BW). Zelfde gedeelde
    # helper + 'toch doorgaan'-override + onuitwisbaar spoor als compose/send.
    from app.collections.compliance import (
        check_dagenbrief_gate_for_case,
        record_dagenbrief_override,
    )

    gate_reason = await check_dagenbrief_gate_for_case(db, user.tenant_id, case_id)
    if gate_reason is not None:
        if not data.compliance_override:
            raise HTTPException(
                status_code=422,
                detail={"code": "DAGENBRIEF_GATE", "message": gate_reason},
            )
        await record_dagenbrief_override(
            db, user.tenant_id, case_id, user.id, gate_reason
        )

    # Resolve body HTML
    if data.body_html:
        body_html = data.body_html
    elif data.body:
        # S227: getypte tekst → echte alinea's met vaste briefmaat (en escape),
        # i.p.v. één platte <br>-blob waar de witregel-regels niet op grepen.
        # Daarna aankleden met de volledige huisstijl (A2): de .eml wordt vanuit
        # Outlook verstuurd, dus dít is de laatste kans — een getypte mail
        # vertrok hier voorheen kaal (zonder logo/handtekening/schuldhulpblok).
        # De AI-concept-flow levert body_html en draagt de opmaak al.
        from app.email.incasso_templates import plain_paragraphs_html

        body_html = await ensure_branded_body(
            db,
            user.tenant_id,
            subject=data.subject,
            body_html=plain_paragraphs_html(data.body),
            case_id=case_id,
            force=True,
        )
    else:
        body_html = ""

    # DF122-07: automatisch factuur-PDF's van claims bijvoegen bij sommatie
    merged_case_file_ids: list[uuid.UUID] = list(data.case_file_ids or [])
    if data.template_type in AUTO_ATTACH_INVOICE_TYPES:
        claims_result = await db.execute(
            select(Claim.invoice_file_id).where(
                Claim.case_id == case_id,
                Claim.tenant_id == user.tenant_id,
                Claim.is_active.is_(True),
                Claim.invoice_file_id.is_not(None),
            )
        )
        invoice_ids = [row[0] for row in claims_result.all() if row[0] is not None]
        # Dedupliceer (gebruiker kan zelf ook facturen toevoegen)
        seen = set(merged_case_file_ids)
        for inv_id in invoice_ids:
            if inv_id not in seen:
                merged_case_file_ids.append(inv_id)
                seen.add(inv_id)

    # Resolve attachments
    attachments = await _resolve_attachments(
        db,
        user.tenant_id,
        case_id,
        merged_case_file_ids or None,
        data.inline_attachments,
    )

    # Punt 1/25 — brieftype afleiden uit de huidige stap als deze verse dossier-mail
    # aan de debiteur geen sjabloontype meedraagt (AI-concept → .eml → Outlook).
    effective_template_type = data.template_type
    if effective_template_type is None:
        effective_template_type = await _derive_step_template_type(case, [data.recipient_email])

    # S212: renteoverzicht-PDF meesturen bij de 14-dagenbrief/eerste sommatie voor een
    # privé aansprakelijke wederpartij — zelfde plek als de factuur-PDF's hierboven. Dit
    # is Lisanne's meest gebruikte route (AI-concept → .eml → Outlook). Leest het
    # opgeslagen rechtsvorm-veld, nooit live de KvK; bij een BV/NV/stichting → geen bijlage.
    for rente_name, rente_bytes, _rente_type in await build_rente_bijlage(
        db, user.tenant_id, case, SimpleNamespace(template_type=effective_template_type), user.id
    ):
        attachments.append(
            OutgoingAttachment(
                filename=rente_name, data=rente_bytes, content_type="application/pdf"
            )
        )

    # S232: totale bijlage-grootte bewaken (geen aantal-limiet meer).
    _assert_total_attachment_size(attachments)

    # Get sender email from connected account (for From header)
    account = await get_email_account(db, user.id, user.tenant_id)
    sender_email = account.email_address if account else (user.email or "")
    sender_name = user.full_name or ""

    # Build .eml (RFC 2822 MIME message)
    msg = EmailMessage()
    msg["Subject"] = data.subject
    msg["To"] = data.recipient_email
    if data.cc:
        msg["Cc"] = ", ".join(data.cc)
    if data.bcc:
        msg["Bcc"] = ", ".join(data.bcc)
    if sender_email:
        msg["From"] = formataddr((sender_name, sender_email))
    # No Date header → Outlook treats it as unsent/draft
    msg["X-Unsent"] = "1"  # Outlook-specific: opens in compose mode

    # Set HTML body
    msg.set_content(body_html, subtype="html")

    # Add attachments
    for att in attachments:
        maintype, _, subtype = att.content_type.partition("/")
        if not subtype:
            maintype, subtype = "application", "octet-stream"
        msg.add_attachment(
            att.data,
            maintype=maintype,
            subtype=subtype,
            filename=att.filename,
        )

    # Log activity on the case
    recipient_label = data.recipient_name or data.recipient_email
    att_count = len(attachments)
    att_text = f", {att_count} bijlage(n)" if att_count else ""
    activity = CaseActivity(
        tenant_id=user.tenant_id,
        case_id=case.id,
        user_id=user.id,
        activity_type="email",
        title=f"E-mail opgesteld voor {recipient_label}",
        description=f"Onderwerp: {data.subject}{att_text}",
    )
    db.add(activity)
    await db.flush()

    # Return .eml file
    eml_bytes = msg.as_bytes()
    filename = f"email-{case.case_number}.eml"

    return Response(
        content=eml_bytes,
        media_type="message/rfc822",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/cases/{case_id}/render-template",
    response_model=RenderTemplateResponse,
)
async def render_template_preview(
    case_id: uuid.UUID,
    data: RenderTemplateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render an incasso template as HTML for email body preview."""
    # Verify case exists
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    # Build context and render
    context = await build_base_context(db, user.tenant_id, case)
    if data.quoted_html:
        context["quoted_html"] = data.quoted_html
    html = render_incasso_email(data.template_type, context)

    if html is None:
        return RenderTemplateResponse(supported=False)

    # Menselijke brieftype-naam: de stapnaam als het gekozen sjabloon de huidige stap
    # is (bv. "Eerste sommatie"), anders de nette title-case van het sjabloontype.
    step = case.incasso_step
    if step is not None and step.template_type == data.template_type and step.name:
        letter_type = step.name
    else:
        letter_type = data.template_type.replace("_", " ").title()

    return RenderTemplateResponse(
        supported=True,
        subject=build_email_subject(
            client_name=case.client.name if case.client else None,
            debtor_name=case.opposing_party.name if case.opposing_party else None,
            letter_type=letter_type,
            case_number=case.case_number,
        ),
        body_html=html,
    )


@router.post(
    "/cases/{case_id}/auto-attachments",
    response_model=AutoAttachmentsResponse,
)
async def preview_auto_attachments(
    case_id: uuid.UUID,
    data: AutoAttachmentsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Punt 2 — toon vóór verzending welke bijlagen automatisch worden meegestuurd.

    Spiegelt de serverlogica van /compose/send zonder de PDF's te renderen: het
    renteoverzicht (bij 14-dagenbrief/eerste sommatie voor een privé aansprakelijke
    debiteur) en de factuur-PDF's (alleen bij een expliciet gekozen sommatie-sjabloon;
    niet op de afgeleide AI-concept-route)."""
    from app.documents.rente_bijlage import (
        VERZOEKSCHRIFT_BIJLAGE_TEMPLATE_TYPES,
        wants_rente_bijlage,
    )

    case = (
        await db.execute(
            select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
        )
    ).scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    # Zelfde afleiding als de verzendknop: geen sjabloontype + mail aan de debiteur →
    # leid het brieftype af uit de huidige stap (voor het renteoverzicht).
    effective_template_type = data.template_type
    if effective_template_type is None and data.recipient_email:
        effective_template_type = await _derive_step_template_type(case, [data.recipient_email])

    items: list[AutoAttachmentItem] = []

    if effective_template_type and wants_rente_bijlage(
        case, SimpleNamespace(template_type=effective_template_type)
    ):
        items.append(
            AutoAttachmentItem(
                label="Renteoverzicht (PDF)",
                kind="rente",
                template_type="renteoverzicht",
            )
        )

    # S225: de dreigbrief belooft het concept-verzoekschrift in de bijlage —
    # de server stuurt hem sindsdien automatisch mee op alle routes.
    if effective_template_type in VERZOEKSCHRIFT_BIJLAGE_TEMPLATE_TYPES:
        items.append(
            AutoAttachmentItem(
                label="Concept-verzoekschrift faillissement (PDF)",
                kind="verzoekschrift",
                template_type="verzoekschrift_faillissement",
            )
        )

    # Factuur-PDF's alleen bij een EXPLICIET gekozen sommatie-sjabloon (geen
    # factuur-auto-attach op de afgeleide route).
    if data.template_type in AUTO_ATTACH_INVOICE_TYPES:
        # S231: één regel per factuur i.p.v. één telling ("3 factuur-PDF's").
        # Alleen zo kan de gebruiker ze stuk voor stuk openen vóór verzending.
        invoice_rows = (
            await db.execute(
                select(CaseFile.id, CaseFile.original_filename)
                .join(Claim, Claim.invoice_file_id == CaseFile.id)
                .where(
                    Claim.case_id == case_id,
                    Claim.tenant_id == user.tenant_id,
                    Claim.is_active.is_(True),
                    Claim.invoice_file_id.is_not(None),
                )
                .distinct()
            )
        ).all()
        for file_id, filename in invoice_rows:
            items.append(
                AutoAttachmentItem(
                    label=filename or "Factuur (PDF)",
                    kind="factuur",
                    case_file_id=file_id,
                )
            )

    return AutoAttachmentsResponse(items=items)


@router.get(
    "/cases/{case_id}/invoice-files",
    response_model=InvoiceFilesResponse,
)
async def list_invoice_files(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """S233 — factuur-PDF's van dit dossier als selecteerbare bijlagen.

    Gebruikt door de AI-antwoord-flow: vraagt de behandelaar "doe de facturen erbij"
    (draft.attach_invoices), dan opent het concept met deze bestanden al aangevinkt.
    Levert alleen de metadata (id/naam/grootte) — het bestand zelf gaat via de
    bestaande case-file-download bij verzending mee. Route-onafhankelijk (geen
    sjabloontype nodig), i.t.t. /auto-attachments dat alleen bij een sommatie-sjabloon
    factuur-PDF's toont."""
    case = (
        await db.execute(
            select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
        )
    ).scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    rows = (
        await db.execute(
            select(CaseFile.id, CaseFile.original_filename, CaseFile.file_size)
            .join(Claim, Claim.invoice_file_id == CaseFile.id)
            .where(
                Claim.case_id == case_id,
                Claim.tenant_id == user.tenant_id,
                Claim.is_active.is_(True),
                Claim.invoice_file_id.is_not(None),
            )
            .distinct()
        )
    ).all()

    return InvoiceFilesResponse(
        items=[
            InvoiceFileItem(
                id=file_id,
                filename=filename or "Factuur (PDF)",
                size=size or 0,
            )
            for file_id, filename, size in rows
        ]
    )
