// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Divider, Flex } from '@geti/ui';

import { Task } from '../../../../core/projects/task.interface';
import { PredictionsSettings } from './prediction-settings/predictions-settings.component';
import { TrainingSettings } from './training-settings/training-settings.component';

interface ActiveLearningConfigurationContentProps {
    selectedTask: Task | null;
}

export const ActiveLearningConfigurationContent: FC<ActiveLearningConfigurationContentProps> = ({ selectedTask }) => {
    return (
        <Flex gap='size-200' direction='column'>
            <PredictionsSettings />

            <Divider size={'S'} />

            <TrainingSettings selectedTask={selectedTask} />
        </Flex>
    );
};
