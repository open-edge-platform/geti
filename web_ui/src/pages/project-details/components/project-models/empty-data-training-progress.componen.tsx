// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Task } from '../../../../core/projects/task.interface';
import { TrainingProgressChainTask } from './training-progress/training-progress-chain-task.component';
import { TrainingProgress } from './training-progress/training-progress.component';

interface EmptyDataTrainingProgressProps {
    isTaskChain: boolean;
    tasks: Task[];
}

export const EmptyDataTrainingProgress = ({ isTaskChain, tasks }: EmptyDataTrainingProgressProps): JSX.Element => {
    if (isTaskChain) {
        return (
            <>
                {tasks.map((task, index) => (
                    <TrainingProgressChainTask task={task} isFirstTask={index === 0} key={task.domain} />
                ))}
            </>
        );
    }

    return <TrainingProgress taskId={tasks[0].id} />;
};
