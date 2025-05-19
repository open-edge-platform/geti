// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, SetStateAction } from 'react';

import { Item, Picker, StyleProps, Text } from '@geti/ui';

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
