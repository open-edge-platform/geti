// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key } from 'react';

import { Item, Picker, Text } from '@geti/ui';

import { Task } from '../../../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

interface TaskSelectionProps {
    tasks: Task[];
    onTaskChange: (task: Task) => void;
    selectedTask: Task;
}

export const TaskSelection: FC<TaskSelectionProps> = ({ tasks, selectedTask, onTaskChange }) => {
    const handleChangeTask = (key: Key) => {
        const task = tasks.find((item) => item.id === key);

        if (task && task.id !== selectedTask.id) {
            onTaskChange(task);
        }
    };

    return (
        <Picker
            items={tasks}
            selectedKey={selectedTask.id}
            onSelectionChange={handleChangeTask}
            aria-label={'Select domain'}
            alignSelf={'flex-end'}
            width={'100%'}
            label={'Task'}
        >
            {(item) => (
                <Item textValue={item.domain} key={item.id} aria-label={item.domain}>
                    <Text id={`${idMatchingFormat(item.domain)}-id`}>{item.domain}</Text>
                </Item>
            )}
        </Picker>
    );
};
