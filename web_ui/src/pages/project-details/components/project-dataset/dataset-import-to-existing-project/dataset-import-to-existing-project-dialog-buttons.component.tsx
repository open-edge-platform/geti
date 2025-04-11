// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { ButtonGroup } from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';
import capitalize from 'lodash/capitalize';

import { DATASET_IMPORT_DIALOG_BUTTONS, DATASET_IMPORT_STATUSES } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportDialogButton, DatasetImportItem } from '../../../../../core/datasets/dataset.interface';
import { getCurrentJob } from '../../../../../core/datasets/utils';
import { useJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { useDatasetImportToExistingProject } from '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { matchStatus } from '../../../../../providers/dataset-import-to-existing-project-provider/utils';
import { useTusUpload } from '../../../../../providers/tus-upload-provider/tus-upload-provider.component';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { Button } from '../../../../../shared/components/button/button.component';
import { isNonEmptyString } from '../../../../../shared/utils';

interface DatasetImportToExistingProjectDialogButtonsProps {
    deletionDialogTriggerState: OverlayTriggerState;
    datasetImportItem: DatasetImportItem | undefined;
    onDialogDismiss: () => void;
    onPrimaryAction: () => void;
}

export const DatasetImportToExistingProjectDialogButtons = ({
    deletionDialogTriggerState,
    datasetImportItem,
    onDialogDismiss,
    onPrimaryAction,
}: DatasetImportToExistingProjectDialogButtonsProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { abortActiveUpload } = useTusUpload();
    const { useCancelJob } = useJobs({ organizationId, workspaceId });
    const { isReady, deleteActiveDatasetImport } = useDatasetImportToExistingProject();

    const abortDatasetImportActionHandler = (importItem: DatasetImportItem) => {
        const currentJobId = getCurrentJob(importItem);

        isNonEmptyString(currentJobId) && useCancelJob.mutateAsync(currentJobId).then(deleteActiveDatasetImport);
    };

    const state = useMemo<DatasetImportDialogButton[]>(
        () => [
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.CANCEL,
                variant: 'primary',
                hidden: !matchStatus(datasetImportItem, [
                    DATASET_IMPORT_STATUSES.UPLOADING,
                    DATASET_IMPORT_STATUSES.PREPARING,
                    DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                ]),
                disabled: !matchStatus(datasetImportItem, [
                    DATASET_IMPORT_STATUSES.UPLOADING,
                    DATASET_IMPORT_STATUSES.PREPARING,
                    DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                ]),
                action: async () => {
                    onDialogDismiss();
                    if (!datasetImportItem) return;

                    matchStatus(datasetImportItem, DATASET_IMPORT_STATUSES.UPLOADING)
                        ? await abortActiveUpload(datasetImportItem.id)
                        : abortDatasetImportActionHandler(datasetImportItem);

                    deleteActiveDatasetImport();
                },
            },
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.DELETE,
                variant: 'negative',
                hidden:
                    !datasetImportItem ||
                    matchStatus(datasetImportItem, [
                        DATASET_IMPORT_STATUSES.UPLOADING,
                        DATASET_IMPORT_STATUSES.PREPARING,
                        DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                    ]),
                disabled:
                    !datasetImportItem ||
                    matchStatus(datasetImportItem, [
                        DATASET_IMPORT_STATUSES.UPLOADING,
                        DATASET_IMPORT_STATUSES.PREPARING,
                        DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                    ]),
                action: () => {
                    if (!datasetImportItem) return;
                    deletionDialogTriggerState.open();
                },
            },
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.HIDE,
                hidden: false,
                disabled: false,
                variant: 'primary',
                action: onDialogDismiss,
            },
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.IMPORT,
                hidden: !matchStatus(datasetImportItem, [
                    DATASET_IMPORT_STATUSES.READY,
                    DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                ]),
                disabled: !isReady(datasetImportItem?.id),
                variant: 'accent',
                action: () => {
                    onPrimaryAction();
                    onDialogDismiss();
                },
            },
        ],
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [
            abortActiveUpload,
            datasetImportItem,
            deleteActiveDatasetImport,
            deletionDialogTriggerState,
            isReady,
            onDialogDismiss,
            onPrimaryAction,
        ]
    );

    return (
        <ButtonGroup>
            {state.map((button: DatasetImportDialogButton) => (
                <Button
                    data-testid={`testid-${button.name}`}
                    key={button.name}
                    variant={button.variant}
                    isHidden={button.hidden}
                    isDisabled={button.disabled}
                    onPress={button.action}
                >
                    {capitalize(button.name)}
                </Button>
            ))}
        </ButtonGroup>
    );
};
