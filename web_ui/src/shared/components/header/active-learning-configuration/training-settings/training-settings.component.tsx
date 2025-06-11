// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Heading, Item, Loading, Picker, View } from '@geti/ui';
import { isNil } from 'lodash-es';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { hasActiveModels } from '../../../../../core/models/utils';
import { Task } from '../../../../../core/projects/task.interface';
import { useProject } from '../../../../../pages/project-details/providers/project-provider/project-provider.component';
import { useActiveLearningConfiguration } from '../use-active-learning-configuration.hook';
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
    const {
        autoTrainingTasks,
        isPending,
        updateRequiredImagesAutoTraining,
        updateDynamicRequiredAnnotations,
        updateAutoTraining,
    } = useActiveLearningConfiguration(projectIdentifier, project.tasks);

    const filteredAutoTrainingTask = isNil(defaultSelectedTask)
        ? autoTrainingTasks
        : autoTrainingTasks.filter(({ task }) => task.id === defaultSelectedTask?.id);

    const autoTrainingTask = filteredAutoTrainingTask.find(({ task }) => task.id === selectedTask);
    const activeModel = modelsData.filter(hasActiveModels).find(({ taskId }) => taskId === autoTrainingTask?.task.id);

    if (isPending || isLoadingModels || autoTrainingTask === undefined) {
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
                projectIdentifier={projectIdentifier}
                onUpdateDynamicRequiredAnnotations={(value) =>
                    updateDynamicRequiredAnnotations(autoTrainingTask.task.id, value)
                }
                onUpdateRequiredImagesAutoTraining={(value) =>
                    updateRequiredImagesAutoTraining(autoTrainingTask.task.id, value)
                }
                onUpdateAutoTraining={(value) => updateAutoTraining(autoTrainingTask.task.id, value)}
            />
        </View>
    );
};
