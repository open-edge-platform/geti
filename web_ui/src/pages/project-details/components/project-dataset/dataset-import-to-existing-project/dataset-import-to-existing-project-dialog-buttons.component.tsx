// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useMemo } from 'react';

import { Button, ButtonGroup, View } from '@geti/ui';
import { OverlayTriggerState } from '@react-stately/overlays';
import { capitalize } from 'lodash-es';

import { DATASET_IMPORT_DIALOG_BUTTONS, DATASET_IMPORT_STATUSES } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportDialogButton, DatasetImportItem } from '../../../../../core/datasets/dataset.interface';
import { getCurrentJob } from '../../../../../core/datasets/utils';
import { useJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { useDatasetImportToExistingProject } from '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { matchStatus } from '../../../../../providers/dataset-import-to-existing-project-provider/utils';
import { useTusUpload } from '../../../../../providers/tus-upload-provider/tus-upload-provider.component';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { isNonEmptyString } from '../../../../../shared/utils';

interface DatasetImportToExistingProjectDialogButtonsProps {
    children?: ReactNode;
    datasetImportItem: DatasetImportItem | undefined;
    isImportDisabled: boolean;
    deletionDialogTriggerState: OverlayTriggerState;
    onDialogDismiss: () => void;
    onPrimaryAction: () => void;
}

export const DatasetImportToExistingProjectDialogButtons = ({
    children,
    datasetImportItem,
    isImportDisabled,
    deletionDialogTriggerState,
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
                disabled: !isReady(datasetImportItem?.id) || isImportDisabled,
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
            <View height={'100%'} marginEnd={'auto'}>
                {children}
            </View>

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
