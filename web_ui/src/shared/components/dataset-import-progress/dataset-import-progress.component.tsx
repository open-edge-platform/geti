// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Loading, Text } from '@geti/ui';

import {
    DATASET_IMPORT_DESCRIPTION,
    DATASET_IMPORT_HEADER,
    DATASET_IMPORT_MESSAGE,
} from '../../../core/datasets/dataset.const';
import { DatasetImportItem } from '../../../core/datasets/dataset.interface';
import { useDatasetImportQueries } from '../../../core/datasets/hooks/use-dataset-import-queries.hook';
import { getJobInfo, isPreparingJob } from '../../../core/datasets/utils';
import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { CircularProgress } from '../circular-progress/circular-progress.component';

import classes from './dataset-import-progress.module.scss';

interface DatasetImportProgressProps {
    progressItem: DatasetImportItem;
}

export const DatasetImportProgress = ({ progressItem }: DatasetImportProgressProps): JSX.Element => {
    const { name, status, timeRemaining } = progressItem;

    const isPreparing = isPreparingJob(progressItem);
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { usePreparingStatusJob } = useDatasetImportQueries();

    const preparingStatusJob = usePreparingStatusJob({
        data: { organizationId, workspaceId, jobId: String(progressItem.preparingJobId) },
        enabled: isPreparing,
    });

    const { description, progress } = isPreparing
        ? getJobInfo(preparingStatusJob.data?.steps, DATASET_IMPORT_MESSAGE[status])
        : { description: DATASET_IMPORT_DESCRIPTION[status], progress: progressItem.progress };

    const header = DATASET_IMPORT_HEADER[status];
    const hasError = header === 'Error';
    const isPreparingJobLoading = isPreparing && progress <= 0;
    const isPreparingJobWithProgress = isPreparing && progress > 0;

    return (
        <div id={'dataset-import-progress'} aria-label={'dataset-import-progress'} style={{ height: '100%' }}>
            <Flex
                direction='column'
                alignItems='center'
                justifyContent='center'
                width='100%'
                height='100%'
                gap='size-400'
                UNSAFE_className={classes.importProgress}
            >
                {(!isPreparing || isPreparingJobWithProgress) && (
                    <CircularProgress
                        hasError={hasError}
                        percentage={progress}
                        size={80}
                        strokeWidth={8}
                        labelFontSize={12}
                        color='gray-500'
                        labelFontColor='gray-700'
                        backStrokeColor='gray-75'
                        checkMarkSize={hasError ? 20 : undefined}
                    />
                )}

                {isPreparingJobLoading && <Loading mode='inline' size='L' style={{ height: 'auto' }} />}

                <Flex direction='column' alignItems='center' justifyContent='center'>
                    <Text id='dataset-import-progress-header' UNSAFE_style={{ fontSize: '2.5em' }}>
                        {header}
                    </Text>
                    <Text id='dataset-import-progress-description'>{description}</Text>
                    <Text id='dataset-import-name' marginTop='size-100'>
                        {name}
                    </Text>
                </Flex>
                <Text id='dataset-import-time-remaining' UNSAFE_className={classes.timeRemaining}>
                    {timeRemaining}
                </Text>
            </Flex>
        </div>
    );
};
