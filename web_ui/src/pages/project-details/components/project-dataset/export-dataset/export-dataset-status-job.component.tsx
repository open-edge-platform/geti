// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode, useState } from 'react';

import { Divider, Flex, Heading, Loading, Text, View } from '@geti/ui';

import { getJobActiveStep } from '../../../../../core/jobs/utils';
import { DatasetIdentifier, ExportDatasetLSData, ExportFormats } from '../../../../../core/projects/dataset.interface';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { JobProgress } from '../../../../../shared/components/header/jobs-management/job-progress.component';
import { ThinProgressBar } from '../../../../../shared/components/thin-progress-bar/thin-progress-bar.component';
import { formatDownloadUrl } from '../../../../../shared/utils';
import { useExportDataset } from '../../../hooks/use-export-dataset.hook';

import classes from '../project-dataset.module.scss';

interface ExportDatasetStatusJobProps {
    datasetIdentifier: DatasetIdentifier;
    onCloseStatus: (id: string) => void;
    localStorageData: ExportDatasetLSData;
    onPrepareDone: (lsData: ExportDatasetLSData) => void;
}

interface ExportDatasetStatusJobWrapperProps {
    exportFormat: ExportFormats;
    datasetName: string;
    children: ReactNode;
}

const ExportDatasetStatusJobWrapper: FC<ExportDatasetStatusJobWrapperProps> = ({
    exportFormat,
    datasetName,
    children,
}) => {
    return (
        <div aria-label='export-dataset-status' className={classes.exportStatusContainer}>
            <View paddingX={'size-200'} paddingTop={'size-200'}>
                <Heading level={6} UNSAFE_className={classes.exportStatusTitle}>
                    Export dataset {`"${datasetName}"`} - {exportFormat.toLocaleUpperCase()} format
                </Heading>
                <Divider size='S' marginTop={'size-100'} />
            </View>
            {children}
        </div>
    );
};

export const ExportDatasetStatusJob = ({
    localStorageData,
    datasetIdentifier,
    onPrepareDone,
    onCloseStatus,
}: ExportDatasetStatusJobProps) => {
    const { addNotification } = useNotification();
    const { datasetId, datasetName } = localStorageData;

    const { useExportDatasetStatusJob } = useExportDataset(datasetName);
    const [isProcessing, setIsProcessing] = useState(true);

    const { organizationId, workspaceId } = datasetIdentifier;

    const { data } = useExportDatasetStatusJob({
        data: {
            organizationId,
            workspaceId,
            jobId: localStorageData.exportDatasetId,
        },
        enabled: isProcessing,
        onSuccess: ({ metadata }) => {
            const downloadUrl = String(metadata.downloadUrl);

            setIsProcessing(false);
            onPrepareDone({
                ...localStorageData,
                downloadUrl: formatDownloadUrl(downloadUrl),
                size: metadata.size,
            });
            addNotification({
                message: `Dataset "${datasetName}" is ready to download`,
                type: NOTIFICATION_TYPE.INFO,
            });
        },
        onCancelOrFailed: () => onCloseStatus(datasetId),
    });

    const jobActiveStep = data !== undefined ? getJobActiveStep(data) : undefined;

    if (data === undefined || jobActiveStep === undefined) {
        return (
            <ExportDatasetStatusJobWrapper
                exportFormat={localStorageData.exportFormat}
                datasetName={localStorageData.datasetName}
            >
                <View padding={'size-200'}>
                    <Flex alignItems={'center'} gap={'size-200'}>
                        <Loading mode='inline' size={'S'} />
                        <Text>Dataset - Processing data, please wait...</Text>
                    </Flex>
                </View>
            </ExportDatasetStatusJobWrapper>
        );
    }

    return (
        <ExportDatasetStatusJobWrapper
            exportFormat={localStorageData.exportFormat}
            datasetName={localStorageData.datasetName}
        >
            <View position={'relative'} padding={'size-200'}>
                <JobProgress step={jobActiveStep} idPrefix={`${datasetId}-export-dataset-progress`} />
                <View position={'absolute'} left={0} bottom={0} right={0}>
                    <ThinProgressBar
                        size='size-25'
                        customColor='var(--energy-blue-shade)'
                        progress={jobActiveStep.progress ?? 0}
                    />
                </View>
            </View>
        </ExportDatasetStatusJobWrapper>
    );
};
