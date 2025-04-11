// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps, FormEvent, ReactNode, useState } from 'react';

import { Flex, TextField } from '@adobe/react-spectrum';

import { Label } from '../../../core/labels/label.interface';
import { Task } from '../../../core/projects/task.interface';
import { onEscape } from '../../utils';
import { TaskLabelTreeContainer } from './task-label-tree-container.component';
import { SearchLabelTreeItemSuffix } from './task-label-tree-item.component';
import { useFilteredTaskMetadata } from './use-filtered-task-metadata.hook';

interface TaskLabelTreeSearchProps {
    id?: string;
    tasks: Task[];
    selectedTask: Task | null;
    includesEmptyLabels?: boolean;
    textFieldProps?: ComponentProps<typeof TextField>;
    onClick: (label: Label) => void;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    ResultWrapper?: (props: { children: ReactNode }) => JSX.Element;
}

const NoopResultWrapper = ({ children }: { children: ReactNode }) => {
    return <>{children}</>;
};

export const TaskLabelTreeSearch = ({
    id,
    tasks,
    selectedTask,
    textFieldProps = {},
    includesEmptyLabels = true,
    suffix,
    prefix,
    onClick,
    ResultWrapper = NoopResultWrapper,
}: TaskLabelTreeSearchProps): JSX.Element => {
    const [input, setInput] = useState(textFieldProps.value ?? '');

    const results = useFilteredTaskMetadata({ input, tasks, selectedTask, includesEmptyLabels });

    const treeItemClickHandler = (label: Label): void => {
        onClick(label);
        setInput('');
    };

    const handleInput = (event: FormEvent<HTMLInputElement>) => {
        setInput(event.currentTarget.value);
    };

    return (
        <Flex gap={'size-100'} direction={'column'} maxHeight={'100%'}>
            <TextField
                id={id ? `${id}-label-search-field-id` : 'label-search-field-id'}
                value={input}
                onInput={handleInput}
                onKeyDown={onEscape((event) => {
                    setInput('');
                    event.currentTarget.blur();
                })}
                {...{
                    width: '100%',
                    placeholder: 'Select label',
                    'aria-label': 'Select label',
                    ...textFieldProps,
                }}
            />
            <ResultWrapper>
                <TaskLabelTreeContainer
                    ariaLabel='label search results'
                    tasksMetadata={results}
                    suffix={suffix}
                    prefix={prefix}
                    onClick={treeItemClickHandler}
                />
            </ResultWrapper>
        </Flex>
    );
};
