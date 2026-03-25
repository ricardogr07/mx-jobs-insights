"""Cloud delivery models shared by pipeline orchestration and tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class UploadedObject:
    """One local artifact mirrored to cloud storage."""

    category: str
    local_path: Path
    object_name: str

    def to_display_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "local_path": str(self.local_path),
            "object_name": self.object_name,
        }


@dataclass(frozen=True, slots=True)
class CloudSyncResult:
    """Result of mirroring local artifacts into Google Cloud Storage."""

    bucket: str
    prefix: str | None
    uploads: tuple[UploadedObject, ...] = ()
    status: str = "not_requested"
    notes: tuple[str, ...] = ()

    @property
    def uploaded_object_count(self) -> int:
        return len(self.uploads)

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "bucket": self.bucket,
            "prefix": self.prefix,
            "uploaded_object_count": self.uploaded_object_count,
            "status": self.status,
            "notes": list(self.notes),
            "uploads": [upload.to_display_dict() for upload in self.uploads],
        }


@dataclass(frozen=True, slots=True)
class BigQueryTableExport:
    """One exported BigQuery table load from local curated or report artifacts."""

    dataset_id: str
    table_name: str
    visibility: str
    row_count: int

    def to_display_dict(self) -> dict[str, str | int]:
        return {
            "dataset_id": self.dataset_id,
            "table_name": self.table_name,
            "visibility": self.visibility,
            "row_count": self.row_count,
        }


@dataclass(frozen=True, slots=True)
class BigQueryExportResult:
    """Result of exporting curated and public-safe tables into BigQuery."""

    project_id: str
    private_dataset: str
    public_dataset: str
    tables: tuple[BigQueryTableExport, ...] = ()
    status: str = "not_requested"
    notes: tuple[str, ...] = ()

    @property
    def private_table_count(self) -> int:
        return sum(1 for table in self.tables if table.visibility == "private")

    @property
    def public_table_count(self) -> int:
        return sum(1 for table in self.tables if table.visibility == "public")

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "private_dataset": self.private_dataset,
            "public_dataset": self.public_dataset,
            "private_table_count": self.private_table_count,
            "public_table_count": self.public_table_count,
            "status": self.status,
            "notes": list(self.notes),
            "tables": [table.to_display_dict() for table in self.tables],
        }
