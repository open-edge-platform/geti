// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Heading, Item, Picker, View } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { hasActiveModels } from '../../../../../core/models/utils';
import { Task } from '../../../../../core/projects/task.interface';
import { useProject } from '../../../../../pages/project-details/providers/project-provider/project-provider.component';
import { Loading } from '../../../loading/loading.component';
import { useAutoTrainingTasksConfig } from '../use-tasks-auto-training-config.hook';
import { AutoTrainingSwitch } from './auto-training-switch.component';

interface TaskPickerProps {
    tasks: Task[];
    selectedTask: string | undefined;
    setSelectedTask: (taskId: string) => void;
}

const TaskPicker = ({ tasks, selectedTask, setSelectedTask }: TaskPickerProps) => {
    if (tasks.length === 1) {
        return null;
    }

    return (
        <Picker
            isQuiet={false}
            aria-label='Select a task to configure its training settings'
            onSelectionChange={(taskId) => setSelectedTask(taskId.toString())}
            selectedKey={selectedTask}
            label={'Task type'}
            width={'100%'}
            marginBottom={'size-200'}
        >
            {tasks.map((task) => {
                return <Item key={task.id}>{task.title}</Item>;
            })}
        </Picker>
    );
};

export const TrainingSettings = ({ selectedTask: defaultSelectedTask }: { selectedTask: Task | null }) => {
    const { project, projectIdentifier } = useProject();
    const [selectedTask, setSelectedTask] = useState(defaultSelectedTask?.id ?? project.tasks.at(0)?.id);

    const { useProjectModelsQuery } = useModels();
    const { data: modelsData = [], isLoading: isLoadingModels } = useProjectModelsQuery();
    const { autoTrainingTasks, isLoading, configParameters } = useAutoTrainingTasksConfig(
        projectIdentifier,
        project.tasks
    );

    const filteredAutoTrainingTask = isNil(defaultSelectedTask)
        ? autoTrainingTasks
        : autoTrainingTasks.filter(({ task }) => task.id === defaultSelectedTask?.id);

    const autoTrainingTask = filteredAutoTrainingTask.find(({ task }) => task.id === selectedTask);
    const activeModel = modelsData.filter(hasActiveModels).find(({ taskId }) => taskId === autoTrainingTask?.task.id);

    if (isLoading || isLoadingModels || configParameters === undefined || autoTrainingTask === undefined) {
        return <Loading />;
    }

    return (
        <View>
            <Heading level={3} margin={0} marginBottom={'size-200'}>
                Training
            </Heading>
            <TaskPicker
                selectedTask={selectedTask}
                setSelectedTask={setSelectedTask}
                tasks={filteredAutoTrainingTask.map(({ task }) => task)}
            />

            <AutoTrainingSwitch
                isTaskChainMode={filteredAutoTrainingTask.length > 1}
                task={autoTrainingTask.task}
                activeModel={activeModel}
                trainingConfig={autoTrainingTask.trainingConfig}
                dynamicRequiredAnnotationsConfig={autoTrainingTask.dynamicRequiredAnnotationsConfig}
                requiredImagesAutoTrainingConfig={autoTrainingTask.requiredImagesAutoTrainingConfig}
                configParameters={configParameters}
                projectIdentifier={projectIdentifier}
            />
        </View>
    );
};
