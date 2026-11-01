from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("apps/api/tests/test_api_flow.py")

HELPER = r'''
def _no_show_demo_files() -> dict[str, tuple[str, bytes, str]]:
    """Build a no-show demo upload with future confirmed appointments.

    Historical rows are preserved exactly as stored in the fixture. Only
    confirmed appointments are moved into a future seven-day window so these
    API tests do not depend on the wall-clock date.
    """
    base = Path("datasets/no-show-demo")
    appointments_path = base / "appointments.csv"

    with appointments_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        assert fieldnames is not None
        appointments = list(reader)

    confirmed = [
        appointment
        for appointment in appointments
        if appointment["status"] == "confirmed"
    ]
    confirmed.sort(
        key=lambda appointment: (
            appointment["scheduled_start"],
            appointment["appointment_id"],
        )
    )

    base_date = (
        datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        + timedelta(days=1)
    )

    for index, appointment in enumerate(confirmed):
        day_offset = index // 4
        slot = index % 4
        scheduled_at = (base_date + timedelta(days=day_offset)).replace(
            hour=8 + (slot * 2),
            minute=0,
            second=0,
            microsecond=0,
        )
        appointment["scheduled_start"] = scheduled_at.isoformat()
        lead_days = 3 + ((index % 4) * 7)
        appointment["created_at"] = (
            scheduled_at - timedelta(days=lead_days)
        ).isoformat()
        appointment["cancelled_at"] = ""

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(appointments)

    return {
        "equipment": (
            "equipment.csv",
            (base / "equipment.csv").read_bytes(),
            "text/csv",
        ),
        "availability": (
            "availability.csv",
            (base / "availability.csv").read_bytes(),
            "text/csv",
        ),
        "appointments": (
            "appointments.csv",
            output.getvalue().encode("utf-8"),
            "text/csv",
        ),
        "executions": (
            "executions.csv",
            (base / "executions.csv").read_bytes(),
            "text/csv",
        ),
    }


'''

NEW_TEST = r'''
def test_no_show_ml_train_and_predict() -> None:
    org_id = create_tenant("ML Tenant")
    uploaded = client.post(
        "/v1/datasets/csv-bundle",
        headers=tenant_headers(org_id, mutate=True),
        files=_no_show_demo_files(),
    )
    assert uploaded.status_code == 201, uploaded.text

    dataset_id = uploaded.json()["dataset"]["id"]
    trained = client.post(
        f"/v1/ml/no-show/train/{dataset_id}",
        headers=tenant_headers(org_id, mutate=True),
    )
    assert trained.status_code == 200, trained.text

    payload = trained.json()
    assert payload["prediction_count"] == 28
    assert payload["actionable_count"] > 0
    assert payload["model_run"]["training_rows"] >= 200
    assert payload["model_run"]["metrics"]["selected_ranking"]["roc_auc"] > 0.5

    predictions = client.get(
        "/v1/ml/no-show/predictions",
        headers=tenant_headers(org_id),
    )
    assert predictions.status_code == 200
    assert len(predictions.json()) == 28


'''

NEW_TRAIN_HELPER = r'''
def _train_no_show_for_tenant(
    org_id: str,
) -> list[dict[str, object]]:
    uploaded = client.post(
        "/v1/datasets/csv-bundle",
        headers=tenant_headers(org_id, mutate=True),
        files=_no_show_demo_files(),
    )
    assert uploaded.status_code == 201, uploaded.text

    dataset_id = uploaded.json()["dataset"]["id"]
    trained = client.post(
        f"/v1/ml/no-show/train/{dataset_id}",
        headers=tenant_headers(org_id, mutate=True),
    )
    assert trained.status_code == 200, trained.text

    predictions = trained.json()["predictions"]
    assert predictions, "Expected no-show predictions to be generated."
    return predictions


'''


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Arquivo não encontrado: {TARGET}")

    source = TARGET.read_text(encoding="utf-8")
    backup = TARGET.with_suffix(".py.bak")
    backup.write_text(source, encoding="utf-8")

    if "import csv\n" not in source:
        source = source.replace("import os\n", "import csv\nimport io\nimport os\n", 1)

    if "from datetime import datetime, timedelta, timezone\n" not in source:
        source = source.replace(
            "from pathlib import Path\n",
            "from datetime import datetime, timedelta, timezone\nfrom pathlib import Path\n",
            1,
        )

    if "def _no_show_demo_files()" not in source:
        marker = "def test_no_show_ml_train_and_predict() -> None:\n"
        if marker not in source:
            raise SystemExit("Não encontrei test_no_show_ml_train_and_predict.")
        source = source.replace(marker, HELPER + marker, 1)

    source, count = re.subn(
        r"def test_no_show_ml_train_and_predict\(\) -> None:\n.*?(?=\ndef _train_no_show_for_tenant\()",
        NEW_TEST.rstrip(),
        source,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit("Não consegui atualizar test_no_show_ml_train_and_predict.")

    source, count = re.subn(
        r"def _train_no_show_for_tenant\(org_id: str\) -> list\[dict\[str, object\]\]:\n.*?(?=\ndef test_no_show_decision_is_persisted_and_idempotently_updated\()",
        NEW_TRAIN_HELPER.rstrip(),
        source,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit("Não consegui atualizar _train_no_show_for_tenant.")

    compile(source, str(TARGET), "exec")
    TARGET.write_text(source, encoding="utf-8")

    print(f"Atualizado: {TARGET}")
    print(f"Backup:     {backup}")
    print("Validação sintática: OK")


if __name__ == "__main__":
    main()
