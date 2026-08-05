"""Regional payment policy defaults for AinerWise Procurement compatibility.

These values are product policy defaults, not live FX quotes. Order/RFQ
commercial snapshots should freeze the authoritative rate used for settlement.
"""

from __future__ import annotations

from copy import deepcopy


FALLBACK_PAYMENT_POLICIES: dict[str, dict] = {
    "RS": {
        "country_name": "Serbia",
        "local_currency": "RSD",
        "local_currency_alias": "DIN",
        "default_settlement_currency": "EUR",
        "default_transaction_mode": "SETTLEMENT_WITH_LOCAL_REFERENCE",
        "enabled_currencies": ["EUR", "RSD"],
        "settlement_currencies": ["EUR", "RSD"],
        "enabled_payment_methods": ["BANK_TRANSFER", "CASH", "CARD_POS"],
        "cross_border_currencies": ["EUR"],
        "force_usd_bridge": False,
        "allow_supplier_payout_currency": True,
        "reference_rates": {"EUR:RSD": "117.20000000", "RSD:EUR": "0.00853242"},
        "rate_source": "STATIC_POLICY_REFERENCE",
    },
    "PL": {
        "country_name": "Poland",
        "local_currency": "PLN",
        "default_settlement_currency": "PLN",
        "default_transaction_mode": "LOCAL_OR_EUR_SETTLEMENT",
        "enabled_currencies": ["PLN", "EUR"],
        "settlement_currencies": ["PLN", "EUR"],
        "enabled_payment_methods": ["BANK_TRANSFER", "CARD_POS"],
        "cross_border_currencies": ["EUR"],
        "force_usd_bridge": False,
        "allow_supplier_payout_currency": True,
        "reference_rates": {"EUR:PLN": "4.30000000", "PLN:EUR": "0.23255814"},
        "rate_source": "STATIC_POLICY_REFERENCE",
    },
    "PH": {
        "country_name": "Philippines",
        "local_currency": "PHP",
        "default_settlement_currency": "PHP",
        "default_transaction_mode": "LOCAL_ONLY",
        "enabled_currencies": ["PHP", "USD"],
        "settlement_currencies": ["PHP", "USD"],
        "enabled_payment_methods": ["BANK_TRANSFER", "CASH_ON_DELIVERY"],
        "cross_border_currencies": ["USD"],
        "force_usd_bridge": False,
        "allow_supplier_payout_currency": True,
        "reference_rates": {},
        "rate_source": "NONE",
    },
    "BA": {
        "country_name": "Bosnia and Herzegovina",
        "local_currency": "BAM",
        "default_settlement_currency": "EUR",
        "default_transaction_mode": "SETTLEMENT_WITH_LOCAL_REFERENCE",
        "enabled_currencies": ["EUR", "BAM"],
        "settlement_currencies": ["EUR", "BAM"],
        "enabled_payment_methods": ["BANK_TRANSFER", "CASH", "CARD_POS"],
        "cross_border_currencies": ["EUR"],
        "force_usd_bridge": False,
        "allow_supplier_payout_currency": True,
        "reference_rates": {"EUR:BAM": "1.95583000", "BAM:EUR": "0.51129188"},
        "rate_source": "STATIC_POLICY_REFERENCE",
    },
    "RO": {
        "country_name": "Romania",
        "local_currency": "RON",
        "default_settlement_currency": "RON",
        "default_transaction_mode": "LOCAL_OR_EUR_SETTLEMENT",
        "enabled_currencies": ["RON", "EUR"],
        "settlement_currencies": ["RON", "EUR"],
        "enabled_payment_methods": ["BANK_TRANSFER", "CARD_POS"],
        "cross_border_currencies": ["EUR"],
        "force_usd_bridge": False,
        "allow_supplier_payout_currency": True,
        "reference_rates": {},
        "rate_source": "REQUIRES_FX_QUOTE",
    },
}


def normalize_country_code(country: str | None) -> str:
    return (country or "RS").strip().upper()[:2] or "RS"


def fallback_payment_policy(country: str | None) -> dict:
    normalized = normalize_country_code(country)
    policy = FALLBACK_PAYMENT_POLICIES.get(normalized) or {
        "country_name": normalized,
        "local_currency": "EUR",
        "default_settlement_currency": "EUR",
        "default_transaction_mode": "LOCAL_ONLY",
        "enabled_currencies": ["EUR"],
        "settlement_currencies": ["EUR"],
        "enabled_payment_methods": ["BANK_TRANSFER"],
        "cross_border_currencies": [],
        "force_usd_bridge": False,
        "allow_supplier_payout_currency": True,
        "reference_rates": {},
        "rate_source": "REQUIRES_REGION_PAYMENT_CONFIG",
    }
    return deepcopy(policy)
