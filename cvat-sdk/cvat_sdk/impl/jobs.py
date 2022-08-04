# Copyright (C) 2022 CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from cvat_sdk import models
from cvat_sdk.impl.downloading import Downloader
from cvat_sdk.impl.model_proxy import ModelProxy
from cvat_sdk.impl.progress import ProgressReporter
from cvat_sdk.impl.uploading import Uploader
from cvat_sdk.models import IJobRead

if TYPE_CHECKING:
    from cvat_sdk.impl.client import Client


class JobProxy(ModelProxy, IJobRead):
    def __init__(self, client: Client, job: models.JobRead):
        ModelProxy.__init__(self, client=client, model=job)

    def fetch(self, force: bool = False):
        # TODO: implement revision checking
        (self._model, _) = self._client.api.jobs_api.retrieve(self.id)

    def commit(self, force: bool = False):
        # TODO: implement revision checking
        self._client.api.jobs_api.partial_update(
            self.id,
            patched_job_write_request=models.PatchedJobWriteRequest(**self._model.to_dict()),
        )

    def import_annotations(
        self,
        format_name: str,
        filename: str,
        *,
        status_check_period: Optional[int] = None,
        pbar: Optional[ProgressReporter] = None,
    ):
        """
        Upload annotations for a job in the specified format (e.g. 'YOLO ZIP 1.0').
        """
        uploader = Uploader(self._client)
        uploader.upload_annotation_file_and_wait(
            self._client.api.jobs_api.create_annotations_endpoint,
            filename,
            format_name,
            url_params={"id": self.id},
            pbar=pbar,
            status_check_period=status_check_period,
        )

        self._client.logger.info(f"Annotation file '{filename}' for job #{self.id} uploaded")

    def export_dataset(
        self,
        format_name: str,
        filename: str,
        *,
        pbar: Optional[ProgressReporter] = None,
        status_check_period: Optional[int] = None,
        include_images: bool = True,
    ) -> None:
        """
        Download annotations for a job in the specified format (e.g. 'YOLO ZIP 1.0').
        """
        if include_images:
            endpoint = self._client.api.tasks_api.retrieve_dataset_endpoint
        else:
            endpoint = self._client.api.tasks_api.retrieve_annotations_endpoint
        downloader = Downloader(self._client)
        downloader.prepare_and_download_file_from_endpoint(
            endpoint=endpoint,
            filename=filename,
            url_params={"id": self.id},
            query_params={"format": format_name},
            pbar=pbar,
            status_check_period=status_check_period,
        )

        self._client.logger.info(f"Dataset for task {self.id} has been downloaded to {filename}")