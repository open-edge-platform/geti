// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Button, ButtonGroup, View } from '@geti/ui';
import { Alert } from '@geti/ui/icons';
import { OverlayTriggerState } from '@react-stately/overlays';
import { capitalize, isEmpty } from 'lodash-es';

import { DATASET_IMPORT_TO_NEW_PROJECT_STEP_TO_STATUS } from '../../../../core/datasets/dataset.const';
import {
    DATASET_IMPORT_DIALOG_BUTTONS,
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../../../core/datasets/dataset.enum';
import { DatasetImportDialogButton, DatasetImportToNewProjectItem } from '../../../../core/datasets/dataset.interface';
import { InfoSection } from '../../../../pages/create-project/components/info-section/info-section.component';
import { matchStatus } from '../../../../providers/dataset-import-to-existing-project-provider/utils';
import { useTusUpload } from '../../../../providers/tus-upload-provider/tus-upload-provider.component';

interface DatasetImportToNewProjectDialogButtonsProps {
    deletionDialogTrigger: OverlayTriggerState;
    datasetImportItem: DatasetImportToNewProjectItem | undefined;
    onDialogDismiss: () => void;
    onPrimaryAction: () => void;
    isReady: (id: string | undefined) => boolean;
    patchDatasetImport: (item: Partial<DatasetImportToNewProjectItem>) => void;
    abortDatasetImportAction: (uploadId: string | null) => void;
    deleteTemporallyDatasetImport: () => void;
}

export const DatasetImportToNewProjectDialogButtons = ({
    isReady,
    onDialogDismiss,
    onPrimaryAction,
    datasetImportItem,
    patchDatasetImport,
    deletionDialogTrigger,
    abortDatasetImportAction,
    deleteTemporallyDatasetImport,
}: DatasetImportToNewProjectDialogButtonsProps): JSX.Element => {
    const { abortActiveUpload } = useTusUpload();

    const noLabelsSelected = datasetImportItem?.labels.length === 0;
    const isClassificationProject = datasetImportItem?.taskType?.includes('classification');
    const showWarning =
        (datasetImportItem?.activeStep === DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS && noLabelsSelected) ||
        (isClassificationProject && datasetImportItem?.labels && datasetImportItem?.labels.length < 2);
    const warningMessage = isClassificationProject
        ? 'Classification projects require at least 2 top level labels'
        : 'Please select at least 1 label';

    const currentStep = useMemo((): DATASET_IMPORT_TO_NEW_PROJECT_STEP => {
        if (!datasetImportItem) return DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET;

        return datasetImportItem.activeStep;
    }, [datasetImportItem]);

    const nextStep = useMemo((): DATASET_IMPORT_TO_NEW_PROJECT_STEP => {
        const steps = Object.values(DATASET_IMPORT_TO_NEW_PROJECT_STEP);
        const stepIdx = steps.findIndex((step: string) => currentStep === step);

        return steps[stepIdx + 1] ?? currentStep;
    }, [currentStep]);

    const previousStep = useMemo((): DATASET_IMPORT_TO_NEW_PROJECT_STEP => {
        const steps = Object.values(DATASET_IMPORT_TO_NEW_PROJECT_STEP);
        const stepIdx = steps.findIndex((step: string) => currentStep === step);

        return steps[stepIdx - 1] ?? currentStep;
    }, [currentStep]);

    const isNextDisabled = useMemo((): boolean => {
        if (!datasetImportItem) return false;

        const { projectName, taskType, supportedProjectTypes } = datasetImportItem;

        if (currentStep === DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET) {
            return isEmpty(supportedProjectTypes);
        }

        if (currentStep === DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN) {
            return isEmpty(projectName) || taskType === null;
        }

        return currentStep === nextStep;
    }, [datasetImportItem, currentStep, nextStep]);

    const state = useMemo<DatasetImportDialogButton[]>(
        () => [
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.CANCEL,
                variant: 'primary',
                hidden: !matchStatus(datasetImportItem, [
                    DATASET_IMPORT_STATUSES.UPLOADING,
                    DATASET_IMPORT_STATUSES.PREPARING,
                    DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                ]),
                disabled: !matchStatus(datasetImportItem, [
                    DATASET_IMPORT_STATUSES.UPLOADING,
                    DATASET_IMPORT_STATUSES.PREPARING,
                    DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                ]),
                action: async () => {
                    onDialogDismiss();
                    if (!datasetImportItem) return;

                    matchStatus(datasetImportItem, DATASET_IMPORT_STATUSES.UPLOADING)
                        ? await abortActiveUpload(datasetImportItem.id)
                        : abortDatasetImportAction(datasetImportItem.uploadId);

                    deleteTemporallyDatasetImport();
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
                        DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                    ]),
                disabled:
                    !datasetImportItem ||
                    matchStatus(datasetImportItem, [
                        DATASET_IMPORT_STATUSES.UPLOADING,
                        DATASET_IMPORT_STATUSES.PREPARING,
                        DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                    ]),
                action: () => {
                    if (!datasetImportItem) return;

                    deletionDialogTrigger.open();
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
                name: DATASET_IMPORT_DIALOG_BUTTONS.BACK,
                hidden:
                    currentStep === previousStep ||
                    !matchStatus(datasetImportItem, [
                        DATASET_IMPORT_STATUSES.READY,
                        DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                        DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                    ]),
                disabled: currentStep === previousStep,
                variant: 'primary',
                action: () => {
                    if (!datasetImportItem) return;

                    patchDatasetImport({
                        id: datasetImportItem.id,
                        activeStep: previousStep,
                    });
                },
            },
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.NEXT,
                hidden:
                    currentStep === nextStep ||
                    !matchStatus(datasetImportItem, [
                        DATASET_IMPORT_STATUSES.READY,
                        DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                        DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                    ]),
                disabled: isNextDisabled,
                variant: 'primary',
                action: () => {
                    if (!datasetImportItem) return;

                    const { id, openedSteps, completedSteps, activeStep } = datasetImportItem;

                    patchDatasetImport({
                        id,
                        activeStep: nextStep,
                        status: DATASET_IMPORT_TO_NEW_PROJECT_STEP_TO_STATUS[nextStep],
                        openedSteps: Array.from(new Set([...openedSteps, nextStep])),
                        completedSteps: Array.from(new Set([...completedSteps, activeStep])),
                    });
                },
            },
            {
                name: DATASET_IMPORT_DIALOG_BUTTONS.CREATE,
                hidden: currentStep !== DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
                disabled: !isReady(datasetImportItem?.id),
                variant: 'accent',
                action: () => {
                    onPrimaryAction();
                    onDialogDismiss();
                },
            },
        ],
        [
            abortActiveUpload,
            abortDatasetImportAction,
            currentStep,
            datasetImportItem,
            deleteTemporallyDatasetImport,
            deletionDialogTrigger,
            isNextDisabled,
            nextStep,
            onDialogDismiss,
            onPrimaryAction,
            patchDatasetImport,
            previousStep,
            isReady,
        ]
    );

    return (
        <ButtonGroup>
            <View UNSAFE_style={{ position: 'absolute', left: 0, top: 0 }}>
                {showWarning ? <InfoSection icon={<Alert />} message={warningMessage} /> : null}
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
