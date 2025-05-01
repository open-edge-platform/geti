// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { InfoTooltip } from '@shared/components/info-tooltip/info-tooltip.component';
import { formatDate } from '@shared/utils';

import { TrainingModelInfoType } from '../../../../../../core/statistics/model-statistics.interface';
import { TrainingMetadataKeys } from '../utils';
import { TrainingModelInfoItem } from './training-model-info-item.component';

import classes from './training-model-info-item.module.scss';

interface TrainingModelInfoProps {
    trainingMetadata: TrainingModelInfoType[];
}

interface TrainingJobDurationProps {
    jobDuration: string;
}

const TrainingJobDuration: FC<TrainingJobDurationProps> = ({ jobDuration }) => {
    return (
        <Flex gap={'size-50'} alignItems={'start'}>
            <TrainingModelInfoItem id={'training-job-duration-id'} value={jobDuration} header={'Job duration'} />
            <InfoTooltip
                id={'job-duration-tooltip-id'}
                tooltipText={
                    'The total time includes loading data, training the model, and evaluating its performance.'
                }
            />
        </Flex>
    );
};

export const TrainingModelInfo: FC<TrainingModelInfoProps> = ({ trainingMetadata }) => {
    const trainingDate = trainingMetadata.find((item) =>
        item.header.toLocaleLowerCase().includes(TrainingMetadataKeys.TRAINING_DATE)
    );
    const trainingTime = trainingMetadata.find((item) =>
        item.header.toLocaleLowerCase().includes(TrainingMetadataKeys.TRAINING_DURATION)
    );
    const trainingJob = trainingMetadata.find((item) =>
        item.header.toLocaleLowerCase().includes(TrainingMetadataKeys.TRAINING_JOB)
    );

    return (
        <Flex gap={'size-600'} marginStart={'size-200'}>
            {trainingDate !== undefined && (
                <TrainingModelInfoItem
                    id={'training-date-id'}
                    value={formatDate(trainingDate.value, 'DD MMMM YYYY')}
                    header={'Training date'}
                    subText={
                        <Text UNSAFE_className={classes.trainingMetadataLabel}>
                            {formatDate(trainingDate.value, 'HH:mm:ss A')}
                        </Text>
                    }
                />
            )}
            {trainingTime !== undefined && (
                <TrainingModelInfoItem
                    id={'training-duration-id'}
                    value={trainingTime.value}
                    header={'Model training time'}
                />
            )}
            {trainingJob !== undefined && <TrainingJobDuration jobDuration={trainingJob.value} />}
        </Flex>
    );
};
