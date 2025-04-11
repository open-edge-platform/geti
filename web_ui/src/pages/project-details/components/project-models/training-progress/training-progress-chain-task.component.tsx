// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Divider, Heading, View } from '@adobe/react-spectrum';

import { Task } from '../../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { TrainingProgress } from './training-progress.component';
import { useTrainingProgress } from './use-training-progress/use-training-progress.hook';

interface TrainingProgressChainTaskProps {
    task: Task;
    isFirstTask: boolean;
}
export const TrainingProgressChainTask = ({ task, isFirstTask }: TrainingProgressChainTaskProps): JSX.Element => {
    const trainingData = useTrainingProgress(task.id);

    if (!trainingData.showTrainingProgress) {
        return <></>;
    }

    const shouldShowDivider = !isFirstTask;
    const taskName = task.domain;

    return (
        <>
            {shouldShowDivider && <Divider size={'S'} marginY={'size-300'} />}
            <View id={`${idMatchingFormat(taskName)}-id`} data-testid={`${idMatchingFormat(taskName)}-id`}>
                <Heading level={2} margin={0}>
                    {taskName}
                </Heading>
                <TrainingProgress taskId={task.id} />
            </View>
        </>
    );
};
