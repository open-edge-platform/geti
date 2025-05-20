// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Heading, View } from '@geti/ui';

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
