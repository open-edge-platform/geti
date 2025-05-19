// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useRef, useState } from 'react';

import { TextField, View } from '@adobe/react-spectrum';
import { CustomPopover } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isFunction } from 'lodash-es';

import { Label } from '../../../core/labels/label.interface';
import { Task } from '../../../core/projects/task.interface';
import { blurActiveInput } from '../../../pages/annotator/tools/utils';
import { runWhen } from '../../utils';
import { TaskLabelTreeContainer } from './task-label-tree-container.component';
import { SearchLabelTreeItemSuffix } from './task-label-tree-item.component';
import { useFilteredTaskMetadata } from './use-filtered-task-metadata.hook';

interface TaskLabelTreeSearchPopoverProps {
    id?: string;
    tasks: Task[];
    isFocus?: boolean;
    selectedTask: Task | null;
    textFieldProps?: ComponentProps<typeof TextField>;
    onClick: (label: Label) => void;
    onClose?: () => void;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
}

const onCloseDialog = runWhen((isOpen: boolean) => !isOpen);

export const TaskLabelTreeSearchPopover = ({
    id,
    tasks,
    selectedTask,
    textFieldProps,
    isFocus = false,
    suffix,
    prefix,
    onClick,
    onClose,
}: TaskLabelTreeSearchPopoverProps): JSX.Element => {
    const triggerRef = useRef(null);
    const [searchInput, setSearchInput] = useState('');

    const dialogState = useOverlayTriggerState({
        onOpenChange: onCloseDialog(() => {
            blurActiveInput(true);
            isFunction(onClose) && onClose();
        }),
    });

    const results = useFilteredTaskMetadata({
        tasks,
        selectedTask,
        input: searchInput,
        includesEmptyLabels: false,
    });

    return (
        <>
            <TextField
                id={id}
                width={'auto'}
                ref={triggerRef}
                value={searchInput}
                autoComplete={'off'}
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus={isFocus}
                {...textFieldProps}
                onFocus={dialogState.open}
                onSelect={dialogState.open}
                onChange={(value) => {
                    setSearchInput(value);
                    dialogState.open();
                }}
            />

            <CustomPopover state={dialogState} ref={triggerRef} placement='bottom left'>
                <View padding={'size-100'} minWidth={'size-3000'} maxHeight={'size-6000'} overflow={'hidden auto'}>
                    <TaskLabelTreeContainer
                        ariaLabel='Label search results'
                        tasksMetadata={results}
                        suffix={suffix}
                        prefix={prefix}
                        onClick={onClick}
                    />
                </View>
            </CustomPopover>
        </>
    );
};
