// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, PropsWithChildren, useRef } from 'react';

import { ActionButton, Divider, Flex, Loading, Text, View } from '@geti/ui';
import { Alert, InfoOutline } from '@geti/ui/icons';
import { OverlayTriggerState } from '@react-stately/overlays';
import { useParams } from 'react-router-dom';

import { DATASET_IMPORT_MESSAGE } from '../../../core/datasets/dataset.const';
import { DATASET_IMPORT_STATUSES } from '../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../core/datasets/dataset.interface';
import { useDatasetImportQueries } from '../../../core/datasets/hooks/use-dataset-import-queries.hook';
import { getJobInfo, isImportingJob, isPreparingJob } from '../../../core/datasets/utils';
import {
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
} from '../../../core/jobs/jobs.interface';
import { getJobActiveStep } from '../../../core/jobs/utils';
import { useStatus } from '../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../core/status/hooks/utils';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { matchStatus } from '../../../providers/dataset-import-to-existing-project-provider/utils';
import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { onValidFileList } from '../../utils';
import { JobListItemProgressStatus } from '../header/jobs-management/jobs-list-item-progress.component';
import { ThinProgressBar } from '../thin-progress-bar/thin-progress-bar.component';
import { DatasetImportPanelMenu } from './dataset-import-panel-menu.component';
import { isDetailsAvailable, isErrorStatus, isUploadingStatus } from './util';

import classes from './dataset-import-panel.module.scss';

export const FILE_FORMAT_ERROR_MESSAGE = 'Only zip files are allowed for upload';

interface DatasetImportPanelProps {
    isDeleting?: boolean;
    datasetImportItem: DatasetImportItem;
    datasetImportDialogTrigger: OverlayTriggerState;
    datasetImportDeleteDialogTrigger: OverlayTriggerState;
    onPrimaryAction: () => void;
    onDeleteAction: () => void;
    isReady: (id: string | undefined) => boolean;
    prepareDataset: (file: File, selectedDatasetId?: string) => string | undefined;
    prepareDatasetAction: (id: string, uploadId: string | null) => void;
    setActiveDatasetImportId: (id: string | undefined) => void;
    abortDatasetImportAction: (uploadId: string | null) => void;
    primaryActionName?: string;
}

const StatusIcon = ({ datasetImportItem }: { datasetImportItem: DatasetImportItem }): JSX.Element => {
    if (isUploadingStatus(datasetImportItem)) {
        return <Loading mode='inline' size={'S'} />;
    }

    if (isErrorStatus(datasetImportItem)) {
        return <Alert className={classes.negative} data-testid='alert-icon' />;
    }

    return <InfoOutline width={16} height={16} data-testid='info-icon' />;
};

interface DatasetImportPanelMessageProps {
    isDeleting: boolean;
    isPreparing: boolean;
    isImporting: boolean;
    status: string;
    preparingJob: JobPrepareDatasetImportNewProjectStatus | undefined;
    importingJob: JobImportDatasetToNewProjectStatus | undefined;
}

const DatasetImportPanelMessageWrapper: FC<PropsWithChildren> = ({ children }) => {
    return <Text id='dataset-import-panel-status-message'>{children}</Text>;
};

const DatasetImportPanelMessage: FC<DatasetImportPanelMessageProps> = ({
    isImporting,
    status,
    isPreparing,
    isDeleting,
    preparingJob,
    importingJob,
}) => {
    if (isDeleting) {
        return <DatasetImportPanelMessageWrapper>Deleting....</DatasetImportPanelMessageWrapper>;
    }

    if (isPreparing) {
        return (
            <DatasetImportPanelMessageWrapper>
                {getJobInfo(preparingJob?.steps, DATASET_IMPORT_MESSAGE[status]).description}
            </DatasetImportPanelMessageWrapper>
        );
    }

    if (isImporting) {
        return (
            <DatasetImportPanelMessageWrapper>
                {getJobInfo(importingJob?.steps, DATASET_IMPORT_MESSAGE[status]).description}
            </DatasetImportPanelMessageWrapper>
        );
    }

    return <DatasetImportPanelMessageWrapper>{DATASET_IMPORT_MESSAGE[status]}</DatasetImportPanelMessageWrapper>;
};

export const DatasetImportPanel: FC<DatasetImportPanelProps> = ({
    isDeleting = false,
    primaryActionName,
    datasetImportItem,
    datasetImportDialogTrigger,
    datasetImportDeleteDialogTrigger,
    isReady,
    onDeleteAction,
    onPrimaryAction,
    prepareDataset,
    prepareDatasetAction,
    setActiveDatasetImportId,
    abortDatasetImportAction,
}) => {
    const { data } = useStatus();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const fileInputRef = useRef<HTMLInputElement>({} as HTMLInputElement);
    const { datasetId } = useParams<{ datasetId?: string }>();
    const { addNotification } = useNotification();
    const { usePreparingStatusJob, useImportingStatusJob } = useDatasetImportQueries();

    const isTryAgainButtonDisabled = isBelowTooLowFreeDiskSpace(data?.freeSpace);

    const isPreparing = isPreparingJob(datasetImportItem);
    const isImporting = isImportingJob(datasetImportItem);

    const preparingStatusJob = usePreparingStatusJob({
        data: { organizationId, workspaceId, jobId: String(datasetImportItem.preparingJobId) },
        enabled: isPreparing,
    });

    const importingStatusJob = useImportingStatusJob({
        data: { organizationId, workspaceId, jobId: String(datasetImportItem.importingJobId) },
        enabled: isImporting,
    });

    const onFileInputChange = onValidFileList(([file]: File[]) => {
        try {
            setActiveDatasetImportId(prepareDataset(file, datasetId));
        } catch (_error: unknown) {
            addNotification({ message: FILE_FORMAT_ERROR_MESSAGE, type: NOTIFICATION_TYPE.ERROR });
        } finally {
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    });

    const getActiveData = () => {
        if (isPreparing) {
            return {
                activeJob: preparingStatusJob.data,
                progress: getJobInfo(preparingStatusJob.data?.steps, DATASET_IMPORT_MESSAGE[datasetImportItem.status])
                    .progress,
            };
        }

        if (isImporting) {
            return {
                activeJob: importingStatusJob.data,
                progress: getJobInfo(importingStatusJob.data?.steps, DATASET_IMPORT_MESSAGE[datasetImportItem.status])
                    .progress,
            };
        }

        return { progress: datasetImportItem.progress, activeJob: undefined };
    };

    const { activeJob, progress } = getActiveData();

    const activeStep = activeJob === undefined ? undefined : getJobActiveStep(activeJob);

    return (
        <div id='dataset-import-panel' aria-label='dataset-import-panel'>
            <View backgroundColor='gray-75' height={115} borderRadius='regular'>
                <Flex direction='column' height='100%'>
                    <Flex flex={4} alignItems='center' justifyContent='space-between' marginX='size-200'>
                        <Text id='dataset-import-panel-header' UNSAFE_style={{ fontWeight: 500 }}>
                            {'Import dataset'} - {datasetImportItem.name} ({datasetImportItem.size})
                        </Text>
                        <DatasetImportPanelMenu
                            isReady={isReady}
                            isDisabled={isDeleting}
                            onDeleteAction={onDeleteAction}
                            onPrimaryAction={onPrimaryAction}
                            setActiveDatasetImportId={setActiveDatasetImportId}
                            abortDatasetImportAction={abortDatasetImportAction}
                            datasetImportItem={datasetImportItem}
                            primaryActionName={primaryActionName}
                            datasetImportDeleteDialogTrigger={datasetImportDeleteDialogTrigger}
                        />
                    </Flex>
                    <Divider size='S' marginX='size-200' />
                    <Flex flex={3} alignItems='center' justifyContent='space-between' marginX='size-200'>
                        <Flex flex={1} alignItems='center' gap='size-400'>
                            <Flex
                                id='dataset-import-panel-status'
                                flex={1}
                                alignItems='center'
                                gap='size-150'
                                marginStart='size-100'
                            >
                                <Text UNSAFE_style={{ display: 'flex' }} id='dataset-import-panel-status-icon'>
                                    <StatusIcon datasetImportItem={datasetImportItem} />
                                </Text>
                                <DatasetImportPanelMessage
                                    isDeleting={isDeleting}
                                    isPreparing={isPreparingJob(datasetImportItem)}
                                    isImporting={isImportingJob(datasetImportItem)}
                                    status={datasetImportItem.status}
                                    preparingJob={preparingStatusJob.data}
                                    importingJob={importingStatusJob.data}
                                />
                            </Flex>
                            {datasetImportItem.status === DATASET_IMPORT_STATUSES.UPLOADING && (
                                <Flex alignItems='center' gap='size-400'>
                                    <Text id='dataset-import-panel-progress'>{progress}%</Text>
                                    <Text id='dataset-import-panel-bytes-remaining'>
                                        {datasetImportItem.bytesRemaining}
                                    </Text>
                                    <Text id='dataset-import-panel-time-remaining'>
                                        {datasetImportItem.timeRemaining}
                                    </Text>
                                </Flex>
                            )}
                            {activeStep !== undefined && (
                                <JobListItemProgressStatus.StepState
                                    idPrefix={'dataset-import-panel'}
                                    step={activeStep}
                                />
                            )}
                        </Flex>

                        {!isDeleting && isDetailsAvailable(datasetImportItem) && (
                            <ActionButton
                                id='dataset-import-panel-see-details-button'
                                isQuiet
                                onPress={() => {
                                    setActiveDatasetImportId(datasetImportItem.id);
                                    datasetImportDialogTrigger.open();
                                }}
                            >
                                See details
                            </ActionButton>
                        )}
                        {datasetImportItem.status === DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT && (
                            <ActionButton
                                id='dataset-import-panel-map-labels-button'
                                isQuiet
                                onPress={() => {
                                    setActiveDatasetImportId(datasetImportItem.id);
                                    datasetImportDialogTrigger.open();
                                }}
                            >
                                Map labels
                            </ActionButton>
                        )}
                        {matchStatus(datasetImportItem, DATASET_IMPORT_STATUSES.PREPARING_ERROR) && (
                            <ActionButton
                                id='dataset-import-panel-try-again-prepare-button'
                                isQuiet
                                onPress={() => prepareDatasetAction(datasetImportItem.id, datasetImportItem.uploadId)}
                                isDisabled={isTryAgainButtonDisabled}
                            >
                                Try again
                            </ActionButton>
                        )}
                        {matchStatus(datasetImportItem, [
                            DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED,
                            DATASET_IMPORT_STATUSES.IMPORTING_ERROR,
                        ]) && (
                            <>
                                <ActionButton
                                    id='dataset-import-panel-try-again-select-file-button'
                                    isQuiet
                                    onPress={() => fileInputRef.current.click()}
                                    isDisabled={isTryAgainButtonDisabled}
                                >
                                    Try again
                                </ActionButton>
                                <input
                                    type='file'
                                    hidden={true}
                                    ref={fileInputRef}
                                    onChange={({ target }) => onFileInputChange(target.files)}
                                    onClick={() => (fileInputRef.current.value = '')}
                                    style={{ pointerEvents: 'all' }}
                                    aria-label='file-input'
                                    accept='.zip'
                                />
                            </>
                        )}
                    </Flex>
                    <ThinProgressBar size='size-25' customColor='var(--energy-blue-shade)' progress={progress} />
                </Flex>
            </View>
        </div>
    );
};
