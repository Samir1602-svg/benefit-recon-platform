"""Pure reconciliation logic for the benefit audit Streamlit application."""

import pandas as pd


KEY_COLUMNS = ("Plan_ID", "Benefit_Service")
AUDIT_FIELDS = {
    "Copay": {
        "label": "Copay",
        "error_type": "Type 1: Financial Mismatch",
        "rule_code": "JA-COPAY-01",
        "fallback_action": "Copay value mismatch.",
    },
    "Coinsurance": {
        "label": "Coinsurance (%)",
        "error_type": "Type 1: Financial Mismatch",
        "rule_code": "JA-COINS-01",
        "fallback_action": "Coinsurance percentage mismatch.",
    },
    "Deductible_Applies": {
        "label": "Deductible Applies Flag",
        "error_type": "Type 2: Policy / Job Aid Clarification",
        "rule_code": "JA-DED-01",
        "fallback_action": "Deductible accumulator mismatch.",
    },
}

DISCREPANCY_COLUMNS = [
    "Plan_ID",
    "Benefit_Service",
    "Field_Audited",
    "Source_Benchmark",
    "System_Coded",
    "Error_Type",
    "Job_Aid_Code",
    "Action_Clarification",
]


def clean_value(value):
    """Normalize common spreadsheet representations before comparison."""
    if pd.isna(value):
        return ""
    return str(value).replace("$", "").replace("%", "").strip().upper()


def validate_input_frames(source, coded):
    """Validate the minimum schema required for a meaningful audit."""
    errors = []
    for label, frame in (("Source", source), ("Coded", coded)):
        missing_keys = [column for column in KEY_COLUMNS if column not in frame.columns]
        if missing_keys:
            errors.append(f"{label} file is missing required columns: {', '.join(missing_keys)}.")

    if errors:
        raise ValueError(" ".join(errors))

    missing_audit_fields = []
    for label, frame in (("Source", source), ("Coded", coded)):
        if not any(field in frame.columns for field in AUDIT_FIELDS):
            missing_audit_fields.append(
                f"{label} file must include at least one audited field: {', '.join(AUDIT_FIELDS)}."
            )
    if missing_audit_fields:
        raise ValueError(" ".join(missing_audit_fields))


def _rule_actions(rules):
    if rules is None:
        return {}
    if isinstance(rules, dict):
        return rules
    return {
        row["rule_code"]: row["clarification_action"]
        for _, row in rules.iterrows()
        if row.get("rule_code") and row.get("clarification_action")
    }


def reconcile_benefits(source, coded, rules=None):
    """Compare source and coded benefit files and return audit-ready results."""
    validate_input_frames(source, coded)
    actions = _rule_actions(rules)
    merged = pd.merge(
        source,
        coded,
        on=list(KEY_COLUMNS),
        suffixes=("_Source", "_Coded"),
        how="outer",
        indicator=True,
    )

    discrepancies = []
    affected_rows = set()

    for row_index, row in merged.iterrows():
        plan = row.get("Plan_ID", "N/A")
        service = row.get("Benefit_Service", "N/A")
        row_key = (plan, service, row_index)

        if row["_merge"] != "both":
            side = "source" if row["_merge"] == "left_only" else "coded"
            missing_side = "coded export" if side == "source" else "source benchmark"
            discrepancies.append({
                "Plan_ID": plan,
                "Benefit_Service": service,
                "Field_Audited": "Benefit row presence",
                "Source_Benchmark": "Present" if side == "source" else "Missing",
                "System_Coded": "Missing" if side == "source" else "Present",
                "Error_Type": "Type 2: Record Presence Clarification",
                "Job_Aid_Code": "RECON-ROW-01",
                "Action_Clarification": f"Benefit row is missing from the {missing_side}.",
            })
            affected_rows.add(row_key)
            continue

        for field, config in AUDIT_FIELDS.items():
            source_column = f"{field}_Source"
            coded_column = f"{field}_Coded"
            if source_column not in merged.columns or coded_column not in merged.columns:
                continue
            if clean_value(row[source_column]) == clean_value(row[coded_column]):
                continue

            discrepancies.append({
                "Plan_ID": plan,
                "Benefit_Service": service,
                "Field_Audited": config["label"],
                "Source_Benchmark": row[source_column],
                "System_Coded": row[coded_column],
                "Error_Type": config["error_type"],
                "Job_Aid_Code": config["rule_code"],
                "Action_Clarification": actions.get(config["rule_code"], config["fallback_action"]),
            })
            affected_rows.add(row_key)

    errors = pd.DataFrame(discrepancies, columns=DISCREPANCY_COLUMNS)
    type1_errors = int(errors["Error_Type"].str.startswith("Type 1", na=False).sum())
    type2_errors = int(errors["Error_Type"].str.startswith("Type 2", na=False).sum())
    total_rows = len(merged)
    affected_row_count = len(affected_rows)
    accuracy = round(((total_rows - affected_row_count) / total_rows) * 100, 1) if total_rows else 100.0

    return {
        "merged": merged,
        "errors": errors,
        "total_rows": total_rows,
        "affected_rows": affected_row_count,
        "type1_errors": type1_errors,
        "type2_errors": type2_errors,
        "accuracy": accuracy,
    }
