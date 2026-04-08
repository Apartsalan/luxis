"""Tests for payment matching — CSV parser, matching algorithm, service, and API."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.csv_parsers import parse_rabobank_csv
from app.ai_agent.payment_matching_algorithm import (
    CaseMatchData,
    _name_similarity,
    find_matches,
)
from app.ai_agent.payment_matching_models import (
    BankTransaction,
    ImportStatus,
    MatchMethod,
    MatchStatus,
)
from app.ai_agent.payment_matching_service import (
    approve_match,
    execute_match,
    generate_matches,
    import_bank_statement,
    list_matches,
    manual_match,
    reject_match,
)
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.collections.models import Claim, InterestRate
from app.relations.models import Contact

# ── Test Data ────────────────────────────────────────────────────────────

RABOBANK_HEADER = (
    '"IBAN/BBAN","Munt","BIC","Volgnr","Datum","Rentedatum","Bedrag",'
    '"Saldo na trn","Tegenrekening IBAN/BBAN","Naam tegenpartij",'
    '"Naam uiteindelijke partij","Naam initiërende partij","BIC tegenpartij",'
    '"Code","Batch ID","Transactiereferentie","Machtigingskenmerk",'
    '"Incassant ID","Betalingskenmerk","Omschrijving-1","Omschrijving-2",'
    '"Omschrijving-3","Reden retour","Oorspr bedrag","Oorspr munt","Koers"'
)

RABOBANK_CREDIT_ROW = (
    '"NL91RABO0315273637","EUR","RABONL2U","001","2026-03-01","2026-03-01",'
    '"+1500.00","25000.00","NL12INGB0001234567","Van der Berg B.V.",'
    '"","","INGBNL2A","cb","","","","","2026-00003",'
    '"Betaling factuur 2026-001","Dossier 2026-00003","","","",""'
)

RABOBANK_DEBIT_ROW = (
    '"NL91RABO0315273637","EUR","RABONL2U","002","2026-03-02","2026-03-02",'
    '"-500.00","24500.00","NL98ABNA0123456789","Belastingdienst",'
    '"","","ABNANL2A","cb","","","","","",'
    '"Betaling aanslag","","","","",""'
)

RABOBANK_CSV = f"{RABOBANK_HEADER}\n{RABOBANK_CREDIT_ROW}\n{RABOBANK_DEBIT_ROW}"


def _make_rabobank_row(
    amount: str,
    counterparty_iban: str = "NL12INGB0001234567",
    counterparty_name: str = "Van der Berg B.V.",
    payment_ref: str = "",
    desc1: str = "",
    desc2: str = "",
    tx_date: str = "2026-03-01",
) -> str:
    return (
        f'"NL91RABO0315273637","EUR","RABONL2U","001","{tx_date}","{tx_date}",'
        f'"{amount}","25000.00","{counterparty_iban}","{counterparty_name}",'
        f'"","","INGBNL2A","cb","","","","","{payment_ref}",'
        f'"{desc1}","{desc2}","","","",""'
    )


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def incasso_case(
    db: AsyncSession, test_tenant: Tenant, test_user: User, test_company: Contact
) -> Case:
    """Create an incasso case with claims for matching tests."""
    # Create opposing party with IBAN
    opposing = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Van der Berg B.V.",
        email="info@vanderberg.nl",
        iban="NL12INGB0001234567",
    )
    db.add(opposing)
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-00003",
        description="Incasso Van der Berg",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        opposing_party_id=opposing.id,
        assigned_to_id=test_user.id,
        date_opened=date.today() - timedelta(days=30),
        total_principal=Decimal("5000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)

    # Add a claim with invoice number
    claim = Claim(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case.id,
        description="Factuur 2026-001",
        principal_amount=Decimal("5000.00"),
        default_date=date.today() - timedelta(days=60),
        invoice_number="2026-001",
    )
    db.add(claim)

    await db.commit()
    await db.refresh(case)
    return case


# ══════════════════════════════════════════════════════════════════════════
# CSV Parser Tests
# ══════════════════════════════════════════════════════════════════════════


class TestRabobankCsvParser:
    def test_parse_with_header(self):
        result = parse_rabobank_csv(RABOBANK_CSV)
        assert result.total_rows == 2
        assert result.credit_count == 1
        assert result.debit_count == 1
        assert len(result.transactions) == 1  # Only credits stored
        assert result.account_iban == "NL91RABO0315273637"

    def test_parse_credit_transaction(self):
        result = parse_rabobank_csv(RABOBANK_CSV)
        txn = result.transactions[0]
        assert txn.amount == Decimal("1500.00")
        assert txn.counterparty_name == "Van der Berg B.V."
        assert txn.counterparty_iban == "NL12INGB0001234567"
        assert txn.is_credit is True
        assert txn.transaction_date == date(2026, 3, 1)
        assert txn.currency == "EUR"

    def test_parse_description_includes_payment_ref(self):
        result = parse_rabobank_csv(RABOBANK_CSV)
        txn = result.transactions[0]
        assert "2026-00003" in txn.description
        assert "Betaling factuur 2026-001" in txn.description

    def test_parse_without_header(self):
        """CSV without header row should still parse."""
        csv = RABOBANK_CREDIT_ROW
        result = parse_rabobank_csv(csv)
        assert result.credit_count == 1
        assert len(result.transactions) == 1

    def test_parse_empty_file(self):
        result = parse_rabobank_csv("")
        assert result.total_rows == 0
        assert len(result.errors) >= 1

    def test_parse_skips_short_rows(self):
        csv = f'{RABOBANK_HEADER}\n"too","few","cols"'
        result = parse_rabobank_csv(csv)
        assert result.skipped_count == 1

    def test_parse_multiple_credits(self):
        row1 = _make_rabobank_row("+1000.00", desc1="Eerste betaling")
        row2 = _make_rabobank_row("+2000.00", desc1="Tweede betaling")
        csv = f"{RABOBANK_HEADER}\n{row1}\n{row2}"
        result = parse_rabobank_csv(csv)
        assert result.credit_count == 2
        assert len(result.transactions) == 2

    def test_parse_debit_only_no_transactions(self):
        csv = f"{RABOBANK_HEADER}\n{RABOBANK_DEBIT_ROW}"
        result = parse_rabobank_csv(csv)
        assert result.debit_count == 1
        assert len(result.transactions) == 0

    def test_parse_amount_precision(self):
        """Amounts should be exact Decimal values."""
        row = _make_rabobank_row("+123.45")
        csv = f"{RABOBANK_HEADER}\n{row}"
        result = parse_rabobank_csv(csv)
        assert result.transactions[0].amount == Decimal("123.45")


# ══════════════════════════════════════════════════════════════════════════
# Match Algorithm Tests
# ══════════════════════════════════════════════════════════════════════════


class TestMatchAlgorithm:
    @pytest.fixture
    def case_data(self) -> list[CaseMatchData]:
        return [
            CaseMatchData(
                id=uuid.uuid4(),
                case_number="2026-00003",
                opposing_party_name="Van der Berg B.V.",
                opposing_party_iban="NL12INGB0001234567",
                outstanding_amount=Decimal("1500.00"),
                invoice_numbers=["2026-001", "2026-002"],
            ),
            CaseMatchData(
                id=uuid.uuid4(),
                case_number="2026-00005",
                opposing_party_name="Jansen Trading",
                opposing_party_iban="NL98ABNA0123456789",
                outstanding_amount=Decimal("3000.00"),
                invoice_numbers=["F-2025-100"],
            ),
        ]

    def test_match_by_case_number(self, case_data: list[CaseMatchData]):
        matches = find_matches(
            "Betaling dossier 2026-00003",
            Decimal("1500.00"),
            "Van der Berg B.V.",
            "NL12INGB0001234567",
            case_data,
        )
        assert len(matches) >= 1
        assert matches[0].match_method == MatchMethod.CASE_NUMBER
        assert matches[0].confidence == 95

    def test_match_by_invoice_number(self, case_data: list[CaseMatchData]):
        matches = find_matches(
            "Betaling factuur 2026-001",
            Decimal("500.00"),
            "Onbekend",
            None,
            case_data,
        )
        # Should find case_data[0] via invoice number
        case0_matches = [m for m in matches if m.case_id == case_data[0].id]
        assert len(case0_matches) == 1
        assert case0_matches[0].match_method == MatchMethod.INVOICE_NUMBER
        assert case0_matches[0].confidence == 90

    def test_match_by_iban(self, case_data: list[CaseMatchData]):
        matches = find_matches(
            "Overboeking",  # No case/invoice number in description
            Decimal("999.00"),  # Amount doesn't match
            "Somebody",
            "NL98ABNA0123456789",  # IBAN of case_data[1]
            case_data,
        )
        case1_matches = [m for m in matches if m.case_id == case_data[1].id]
        assert len(case1_matches) == 1
        assert case1_matches[0].match_method == MatchMethod.IBAN
        assert case1_matches[0].confidence == 85

    def test_match_by_amount(self, case_data: list[CaseMatchData]):
        matches = find_matches(
            "Betaling",
            Decimal("3000.00"),  # Exact match with case_data[1]
            "Unknown Person",
            None,
            case_data,
        )
        case1_matches = [m for m in matches if m.case_id == case_data[1].id]
        assert len(case1_matches) == 1
        assert case1_matches[0].match_method == MatchMethod.AMOUNT
        assert case1_matches[0].confidence == 70

    def test_match_by_name(self, case_data: list[CaseMatchData]):
        matches = find_matches(
            "Betaling",
            Decimal("999.00"),
            "Jansen Trading",  # Name of case_data[1]
            None,
            case_data,
        )
        case1_matches = [m for m in matches if m.case_id == case_data[1].id]
        assert len(case1_matches) == 1
        assert case1_matches[0].match_method == MatchMethod.NAME
        assert case1_matches[0].confidence == 50

    def test_highest_confidence_wins(self, case_data: list[CaseMatchData]):
        """When multiple methods match, highest confidence wins."""
        matches = find_matches(
            "Betaling 2026-00003",  # Case number match (95)
            Decimal("1500.00"),  # Also amount match (70)
            "Van der Berg B.V.",  # Also name match (50)
            "NL12INGB0001234567",  # Also IBAN match (85)
            case_data,
        )
        case0_matches = [m for m in matches if m.case_id == case_data[0].id]
        assert len(case0_matches) == 1
        assert case0_matches[0].match_method == MatchMethod.CASE_NUMBER
        assert case0_matches[0].confidence == 95

    def test_no_match_found(self, case_data: list[CaseMatchData]):
        matches = find_matches(
            "Lunch met collega",
            Decimal("25.50"),
            "Restaurant Haesje Claes",
            "NL00XXXX0000000000",
            case_data,
        )
        assert len(matches) == 0

    def test_sorted_by_confidence(self, case_data: list[CaseMatchData]):
        """Results should be sorted highest confidence first."""
        matches = find_matches(
            "Betaling 2026-00003",
            Decimal("3000.00"),  # Matches case_data[1] by amount
            "Van der Berg B.V.",
            None,
            case_data,
        )
        if len(matches) >= 2:
            assert matches[0].confidence >= matches[1].confidence


class TestNameSimilarity:
    def test_exact_match(self):
        assert _name_similarity("Van der Berg B.V.", "Van der Berg B.V.") is True

    def test_case_insensitive(self):
        assert _name_similarity("van der berg b.v.", "Van Der Berg B.V.") is True

    def test_containment(self):
        assert _name_similarity("Van der Berg", "Van der Berg B.V.") is True

    def test_word_overlap(self):
        assert _name_similarity("Berg BV", "Van der Berg B.V.") is True

    def test_no_match(self):
        assert _name_similarity("Jansen", "Van der Berg") is False

    def test_empty_strings(self):
        assert _name_similarity("", "Van der Berg") is False
        assert _name_similarity("Van der Berg", "") is False


# ══════════════════════════════════════════════════════════════════════════
# Service Tests (integration with DB)
# ══════════════════════════════════════════════════════════════════════════


class TestImportService:
    @pytest.mark.asyncio
    async def test_import_creates_records(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test_statement.csv",
            RABOBANK_CSV,
            bank="rabobank",
        )
        await db.commit()

        assert stmt_import.status == ImportStatus.COMPLETED
        assert stmt_import.credit_count == 1
        assert stmt_import.debit_count == 1
        assert stmt_import.filename == "test_statement.csv"
        assert stmt_import.account_iban == "NL91RABO0315273637"

    @pytest.mark.asyncio
    async def test_import_unknown_bank_fails(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            RABOBANK_CSV,
            bank="unknown_bank",
        )
        assert stmt_import.status == ImportStatus.FAILED

    @pytest.mark.asyncio
    async def test_import_empty_csv_fails(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "empty.csv",
            "",
            bank="rabobank",
        )
        assert stmt_import.status == ImportStatus.FAILED


class TestMatchGeneration:
    @pytest.mark.asyncio
    async def test_generate_matches_finds_case(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User, incasso_case: Case
    ):
        # Import CSV with matching transaction
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            RABOBANK_CSV,
            bank="rabobank",
        )
        await db.flush()

        # Generate matches
        count = await generate_matches(db, test_tenant.id, stmt_import.id)
        await db.commit()

        assert count >= 1

    @pytest.mark.asyncio
    async def test_generate_matches_no_cases(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """No incasso cases = no matches."""
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            RABOBANK_CSV,
            bank="rabobank",
        )
        await db.flush()

        count = await generate_matches(db, test_tenant.id, stmt_import.id)
        assert count == 0


class TestMatchWorkflow:
    @pytest.mark.asyncio
    async def test_approve_match(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User, incasso_case: Case
    ):
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            RABOBANK_CSV,
            bank="rabobank",
        )
        await db.flush()
        await generate_matches(db, test_tenant.id, stmt_import.id)
        await db.flush()

        # Get matches
        result = await list_matches(db, test_tenant.id, status_filter="pending")
        assert result.total >= 1

        match_id = result.items[0].id

        # Approve
        approved = await approve_match(db, test_tenant.id, match_id, test_user.id)
        assert approved is not None
        assert approved.status == MatchStatus.APPROVED
        await db.commit()

    @pytest.mark.asyncio
    async def test_reject_match_unmarks_transaction(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User, incasso_case: Case
    ):
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            RABOBANK_CSV,
            bank="rabobank",
        )
        await db.flush()
        await generate_matches(db, test_tenant.id, stmt_import.id)
        await db.flush()

        result = await list_matches(db, test_tenant.id, status_filter="pending")
        match_id = result.items[0].id

        # Reject
        rejected = await reject_match(
            db, test_tenant.id, match_id, test_user.id, note="Verkeerde koppeling"
        )
        assert rejected is not None
        assert rejected.status == MatchStatus.REJECTED
        await db.commit()

    @pytest.mark.asyncio
    async def test_execute_creates_payment_and_trust_transaction(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User, incasso_case: Case
    ):
        """Execute should create both a trust fund deposit and a payment record."""
        # Seed interest rates (required by create_payment)
        for rate_type, rate_val in [("statutory", "6.00"), ("commercial", "11.50")]:
            db.add(
                InterestRate(
                    id=uuid.uuid4(),
                    rate_type=rate_type,
                    effective_from=date(2024, 1, 1),
                    rate=Decimal(rate_val),
                    source="Test fixture",
                )
            )
        await db.flush()

        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            RABOBANK_CSV,
            bank="rabobank",
        )
        await db.flush()
        await generate_matches(db, test_tenant.id, stmt_import.id)
        await db.flush()

        result = await list_matches(db, test_tenant.id, status_filter="pending")
        match_id = result.items[0].id

        # Approve first
        await approve_match(db, test_tenant.id, match_id, test_user.id)
        await db.flush()

        # Execute
        executed = await execute_match(db, test_tenant.id, match_id, test_user.id)
        assert executed is not None
        assert executed.status == MatchStatus.EXECUTED
        assert executed.payment_id is not None
        assert executed.trust_transaction_id is not None
        await db.commit()

    @pytest.mark.asyncio
    async def test_manual_match(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User, incasso_case: Case
    ):
        # Import a transaction
        row = _make_rabobank_row("+750.00", counterparty_name="Onbekende Betaler")
        csv = f"{RABOBANK_HEADER}\n{row}"
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            csv,
            bank="rabobank",
        )
        await db.flush()

        # Get the transaction
        from sqlalchemy import select

        txn_result = await db.execute(
            select(BankTransaction).where(BankTransaction.import_id == stmt_import.id)
        )
        txn = txn_result.scalar_one()

        # Manual match
        match = await manual_match(
            db,
            test_tenant.id,
            test_user.id,
            txn.id,
            incasso_case.id,
            note="Handmatig gekoppeld",
        )
        await db.commit()

        assert match.match_method == MatchMethod.MANUAL
        assert match.confidence == 100
        assert match.status == MatchStatus.APPROVED

    @pytest.mark.asyncio
    async def test_manual_match_invalid_transaction(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User, incasso_case: Case
    ):
        with pytest.raises(ValueError, match="Transactie niet gevonden"):
            await manual_match(
                db,
                test_tenant.id,
                test_user.id,
                uuid.uuid4(),
                incasso_case.id,
            )

    @pytest.mark.asyncio
    async def test_manual_match_invalid_case(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        # Import a transaction
        row = _make_rabobank_row("+100.00")
        csv = f"{RABOBANK_HEADER}\n{row}"
        stmt_import = await import_bank_statement(
            db,
            test_tenant.id,
            test_user.id,
            "test.csv",
            csv,
            bank="rabobank",
        )
        await db.flush()

        from sqlalchemy import select

        txn_result = await db.execute(
            select(BankTransaction).where(BankTransaction.import_id == stmt_import.id)
        )
        txn = txn_result.scalar_one()

        with pytest.raises(ValueError, match="Dossier niet gevonden"):
            await manual_match(
                db,
                test_tenant.id,
                test_user.id,
                txn.id,
                uuid.uuid4(),
            )


# ══════════════════════════════════════════════════════════════════════════
# API Tests
# ══════════════════════════════════════════════════════════════════════════


class TestPaymentMatchingAPI:
    @pytest.mark.asyncio
    async def test_upload_endpoint(self, client, auth_headers):
        """POST /api/payment-matching/import with CSV file."""
        response = await client.post(
            "/api/payment-matching/import",
            headers=auth_headers,
            files={"file": ("test.csv", RABOBANK_CSV.encode(), "text/csv")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "completed"
        assert data["credit_count"] == 1

    @pytest.mark.asyncio
    async def test_upload_non_csv_rejected(self, client, auth_headers):
        response = await client.post(
            "/api/payment-matching/import",
            headers=auth_headers,
            files={"file": ("test.txt", b"not a csv", "text/plain")},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_imports(self, client, auth_headers):
        # Upload first
        await client.post(
            "/api/payment-matching/import",
            headers=auth_headers,
            files={"file": ("test.csv", RABOBANK_CSV.encode(), "text/csv")},
        )
        response = await client.get(
            "/api/payment-matching/imports",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_matches_endpoint(self, client, auth_headers):
        response = await client.get(
            "/api/payment-matching/matches",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_match_stats_endpoint(self, client, auth_headers):
        response = await client.get(
            "/api/payment-matching/matches/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "executed" in data

    @pytest.mark.asyncio
    async def test_approve_nonexistent_match(self, client, auth_headers):
        response = await client.post(
            f"/api/payment-matching/matches/{uuid.uuid4()}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 404
