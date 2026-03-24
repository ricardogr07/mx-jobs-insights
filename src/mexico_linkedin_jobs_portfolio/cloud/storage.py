"""Google Cloud Storage publication helpers for Phase 5 cloud delivery."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from mexico_linkedin_jobs_portfolio.config.cloud import CloudEnvironmentConfig
from mexico_linkedin_jobs_portfolio.models.cloud import CloudSyncResult, UploadedObject


class BlobProtocol(Protocol):
    def upload_from_filename(self, filename: str) -> None: ...


class BucketProtocol(Protocol):
    def blob(self, blob_name: str) -> BlobProtocol: ...


class StorageClientProtocol(Protocol):
    def bucket(self, bucket_name: str) -> BucketProtocol: ...


class CloudArtifactPublisher:
    """Mirror local curated, report, site, and diagnostic artifacts into GCS."""

    def __init__(self, storage_client: StorageClientProtocol | None = None) -> None:
        self.storage_client = storage_client

    def publish(
        self,
        cloud_config: CloudEnvironmentConfig,
        *,
        curated_root: Path,
        report_root: Path,
        site_output_root: Path | None,
        diagnostics_paths: tuple[Path, ...] = (),
    ) -> CloudSyncResult:
        uploads = self.plan_uploads(
            cloud_config,
            curated_root=curated_root,
            report_root=report_root,
            site_output_root=site_output_root,
            diagnostics_paths=diagnostics_paths,
        )
        if not uploads:
            return CloudSyncResult(
                bucket=cloud_config.gcs_bucket or "",
                prefix=cloud_config.normalized_gcs_prefix or None,
                status="gcs_publish_skipped",
                notes=("No cloud artifacts were selected for upload.",),
            )

        bucket = self._storage_client().bucket(cloud_config.gcs_bucket or "")
        for upload in uploads:
            bucket.blob(upload.object_name).upload_from_filename(str(upload.local_path))

        return CloudSyncResult(
            bucket=cloud_config.gcs_bucket or "",
            prefix=cloud_config.normalized_gcs_prefix or None,
            uploads=uploads,
            status="gcs_published",
            notes=(
                f"Uploaded {len(uploads)} artifact(s) to {cloud_config.bucket_uri or cloud_config.gcs_bucket}.",
            ),
        )

    def plan_uploads(
        self,
        cloud_config: CloudEnvironmentConfig,
        *,
        curated_root: Path,
        report_root: Path,
        site_output_root: Path | None,
        diagnostics_paths: tuple[Path, ...] = (),
    ) -> tuple[UploadedObject, ...]:
        uploads: list[UploadedObject] = []
        uploads.extend(self._collect_tree_uploads("curated", Path(curated_root), cloud_config))
        uploads.extend(self._collect_tree_uploads("reports", Path(report_root), cloud_config))
        if site_output_root is not None:
            uploads.extend(self._collect_tree_uploads("site", Path(site_output_root), cloud_config))
        uploads.extend(self._collect_diagnostic_uploads(diagnostics_paths, cloud_config))
        return tuple(uploads)

    def _storage_client(self) -> StorageClientProtocol:
        if self.storage_client is not None:
            return self.storage_client

        try:
            from google.cloud import storage  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised via fake clients in tests.
            raise RuntimeError(
                "Cloud storage publishing requires google-cloud-storage or an injected storage client."
            ) from exc
        return storage.Client()

    def _collect_tree_uploads(
        self,
        category: str,
        root: Path,
        cloud_config: CloudEnvironmentConfig,
    ) -> list[UploadedObject]:
        root = root.expanduser().resolve(strict=False)
        if not root.exists():
            return []

        uploads: list[UploadedObject] = []
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            relative = path.relative_to(root).as_posix()
            uploads.append(
                UploadedObject(
                    category=category,
                    local_path=path,
                    object_name=self._object_name(cloud_config, category, relative),
                )
            )
        return uploads

    def _collect_diagnostic_uploads(
        self,
        diagnostics_paths: tuple[Path, ...],
        cloud_config: CloudEnvironmentConfig,
    ) -> list[UploadedObject]:
        uploads: list[UploadedObject] = []
        for path in diagnostics_paths:
            if path is None:
                continue
            candidate = Path(path).expanduser().resolve(strict=False)
            if not candidate.is_file():
                continue
            relative = candidate.name
            if "reports" in candidate.parts:
                relative = "/".join(candidate.parts[candidate.parts.index("reports") :])
            elif "site" in candidate.parts:
                relative = "site/" + candidate.name
            elif "pipeline" in candidate.parts:
                relative = "pipeline/" + candidate.name
            uploads.append(
                UploadedObject(
                    category="diagnostics",
                    local_path=candidate,
                    object_name=self._object_name(cloud_config, "diagnostics", relative),
                )
            )
        return uploads

    @staticmethod
    def _object_name(cloud_config: CloudEnvironmentConfig, category: str, relative: str) -> str:
        segments = [segment for segment in (cloud_config.normalized_gcs_prefix, category, relative) if segment]
        return "/".join(segment.strip("/") for segment in segments)
