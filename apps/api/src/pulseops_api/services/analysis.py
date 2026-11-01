from __future__ import annotations

from oie_core.portfolio import analyze_operations

from pulseops_api.services.ingestion import OperationalDataset


def analyze_dataset(dataset: OperationalDataset):
    return analyze_operations(
        equipment=dataset.equipment,
        availability=dataset.availability,
        appointments=dataset.appointments,
        executions=dataset.executions,
    )
