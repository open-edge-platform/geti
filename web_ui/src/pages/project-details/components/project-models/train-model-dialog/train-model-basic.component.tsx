// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Text, View } from '@geti/ui';

import { Task } from '../../../../../core/projects/task.interface';
import { SupportedAlgorithm } from '../../../../../core/supported-algorithms/supported-algorithms.interface';
import { ModelTypesList } from './model-types/model-types-list.component';
import { TaskSelection } from './model-types/task-selection.component';

import classes from './train-model-basic.module.scss';

interface TrainModelBasicProps {
    algorithms: SupportedAlgorithm[];
    activeModelTemplateId: string | null;
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    tasks: Task[];
    selectedTask: Task;
    onTaskChange: (task: Task) => void;
    isTaskChainProject: boolean;
}

export const TrainModelBasic: FC<TrainModelBasicProps> = ({
    algorithms,
    activeModelTemplateId,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    onTaskChange,
    selectedTask,
    tasks,
    isTaskChainProject,
}) => {
    return (
        <Flex direction={'column'} gap={'size-200'}>
            {isTaskChainProject && (
                <TaskSelection tasks={tasks} onTaskChange={onTaskChange} selectedTask={selectedTask} />
            )}

            <View padding={'size-250'} backgroundColor={'gray-50'}>
                <Text UNSAFE_className={classes.title} marginBottom={'size-100'}>
                    Model type
                </Text>
                <ModelTypesList
                    algorithms={algorithms}
                    selectedModelTemplateId={selectedModelTemplateId}
                    onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                    activeModelTemplateId={activeModelTemplateId}
                />
            </View>
        </Flex>
    );
};
