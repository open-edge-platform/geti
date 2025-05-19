// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key } from 'react';

import { Item, Picker, Text } from '@geti/ui';

import { Task } from '../../../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

interface TaskSelectionProps {
    tasks: Task[];
    onTaskChange: (task: Key) => void;
    selectedTask: string;
}

export const TaskSelection: FC<TaskSelectionProps> = ({ tasks, selectedTask, onTaskChange }) => {
    return (
        <Picker
            items={tasks}
            selectedKey={selectedTask}
            onSelectionChange={onTaskChange}
            aria-label={'Select domain'}
            alignSelf={'flex-end'}
            width={'100%'}
            label={'Task'}
        >
            {(item) => (
                <Item textValue={item.domain} key={item.domain} aria-label={item.domain}>
                    <Text id={`${idMatchingFormat(item.domain)}-id`}>{item.domain}</Text>
                </Item>
            )}
        </Picker>
    );
};
