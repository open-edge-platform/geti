// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC, Key } from 'react';

import { Item, Picker, Text } from '@adobe/react-spectrum';

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
