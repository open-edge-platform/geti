// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Divider, Flex } from '@adobe/react-spectrum';

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
