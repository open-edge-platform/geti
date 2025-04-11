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
