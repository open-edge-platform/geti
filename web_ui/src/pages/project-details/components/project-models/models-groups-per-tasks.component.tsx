// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { memo, useMemo } from 'react';

import { Divider, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { ModelGroupsAlgorithmDetails } from '../../../../core/models/models.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isNotCropTask } from '../../../../shared/utils';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { ModelsGroupsSingleTask } from './models-groups-single-task.component';
import { TrainingProgressChainTask } from './training-progress/training-progress-chain-task.component';

interface ModelsPerTaskProps {
    modelsGroups: ModelGroupsAlgorithmDetails[];
    tasks: Task[];
}

interface ModelsGroupsGroupedByTaskProps {
    modelsGroups: ModelGroupsAlgorithmDetails[];
    task: Task;
}

const useGetModelsGroupsGroupedByTask = (
    inputModelsGroups: ModelGroupsAlgorithmDetails[],
    tasks: Task[]
): ModelsGroupsGroupedByTaskProps[] => {
    return useMemo(() => {
        const modelsWithTaskNames = tasks.filter(isNotCropTask).map((task) => {
            const modelsGroups = inputModelsGroups.filter((group) => group.taskId === task.id);

            return {
                task,
                modelsGroups,
            };
        });

        return modelsWithTaskNames;
    }, [inputModelsGroups, tasks]);
};

export const ModelsGroupsPerTasks = memo(({ modelsGroups, tasks }: ModelsPerTaskProps): JSX.Element => {
    const modelsGroupedByTask = useGetModelsGroupsGroupedByTask(modelsGroups, tasks);

    return (
        <>
            {modelsGroupedByTask.map((modelsGroupsByTask, index) => {
                const { task } = modelsGroupsByTask;
                const shouldShowDivider = index !== 0 && modelsGroupedByTask.length > 1;
                const taskName = task.domain;

                return isEmpty(modelsGroupsByTask.modelsGroups) ? (
                    <TrainingProgressChainTask task={task} isFirstTask={index === 0} key={taskName} />
                ) : (
                    <View data-testid={`${idMatchingFormat(taskName)}-id`} key={taskName}>
                        {shouldShowDivider && <Divider size={'S'} marginY={'size-300'} />}

                        <ModelsGroupsSingleTask modelsGroups={modelsGroupsByTask.modelsGroups} taskName={taskName} />
                    </View>
                );
            })}
        </>
    );
});
