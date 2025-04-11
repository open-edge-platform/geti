// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, Key, SetStateAction } from 'react';

import { Item, Picker } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';
import { StyleProps } from '@react-types/shared';

import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { TasksItems } from '../../project-models/project-models.interface';

interface TasksListProps {
    items: TasksItems[];
    selectedTask: string;
    setSelectedTask: Dispatch<SetStateAction<string>> | ((inputValue: Key) => void);
    marginTop?: StyleProps['marginTop'];
    marginBottom?: StyleProps['marginBottom'];
}

export const TasksList = ({
    items,
    selectedTask,
    setSelectedTask,
    marginTop,
    marginBottom,
}: TasksListProps): JSX.Element => {
    return (
        <Picker
            isQuiet
            items={items}
            selectedKey={selectedTask}
            onSelectionChange={(key) => setSelectedTask(String(key))}
            marginTop={marginTop}
            marginBottom={marginBottom}
            aria-label={'Select task'}
            id={'task-selection-id'}
        >
            {(item) => (
                <Item key={item.path ?? item.domain} textValue={item.domain}>
                    <Text id={`${idMatchingFormat(item.domain)}-id`}>{item.domain}</Text>
                </Item>
            )}
        </Picker>
    );
};
