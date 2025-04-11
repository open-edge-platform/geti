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

import { useRef, useState } from 'react';

import { TextField, View } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { Label } from '../../../../core/labels/label.interface';
import { CustomPopover } from '../../../../shared/components/custom-popover/custom-popover.component';
import { TaskLabelTreeContainer } from '../../../../shared/components/task-label-tree-search/task-label-tree-container.component';
import { useFilteredTaskMetadata } from '../../../../shared/components/task-label-tree-search/use-filtered-task-metadata.hook';
import { getAvailableLabelsWithoutEmpty } from '../../annotation/labels/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { blurActiveInput } from '../../tools/utils';
import { HierarchicalLabelView } from '../labels/hierarchical-label-view/hierarchical-label-view.component';

interface DefaultLabelComboboxProps {
    defaultLabel?: Label | null;
    setDefaultLabel: (label: Label | null) => void;
}

export const DefaultLabelCombobox = ({ defaultLabel, setDefaultLabel }: DefaultLabelComboboxProps): JSX.Element => {
    const triggerRef = useRef(null);
    const { tasks, selectedTask } = useTask();
    const [searchInput, setSearchInput] = useState('');
    const [shouldFocusTextInput, setShouldFocusTextInput] = useState(false);

    const dialogState = useOverlayTriggerState({
        onOpenChange: (isOpen) => {
            if (!isOpen) {
                blurActiveInput(true);
            }
        },
    });

    const results = useFilteredTaskMetadata({
        tasks,
        selectedTask,
        input: searchInput,
        includesEmptyLabels: false,
    });

    if (!defaultLabel || shouldFocusTextInput) {
        return (
            <div style={{ position: 'relative' }}>
                <TextField
                    id={'label-search-field-id'}
                    width={'auto'}
                    minWidth={'size-2000'}
                    ref={triggerRef}
                    value={searchInput}
                    autoComplete={'off'}
                    // eslint-disable-next-line jsx-a11y/no-autofocus
                    autoFocus={shouldFocusTextInput}
                    aria-label={'Select default label'}
                    placeholder={'Select default label'}
                    onSelect={dialogState.open}
                    onFocus={dialogState.open}
                    onChange={(value) => {
                        setSearchInput(value);
                        dialogState.open();
                    }}
                />

                <CustomPopover state={dialogState} ref={triggerRef}>
                    <View padding={'size-100'} minWidth={'size-3000'} maxHeight={'31.2rem'} overflow={'hidden auto'}>
                        <TaskLabelTreeContainer
                            ariaLabel='Label search results'
                            tasksMetadata={results}
                            onClick={(label: Label) => {
                                setDefaultLabel(label);
                                setShouldFocusTextInput(false);
                            }}
                        />
                    </View>
                </CustomPopover>
            </div>
        );
    }

    return (
        <div id='selected-default-label' data-testid='default-label-id' aria-label='Selected default label'>
            <HierarchicalLabelView
                isPointer
                label={defaultLabel}
                labels={getAvailableLabelsWithoutEmpty(tasks, selectedTask)}
                resetHandler={() => {
                    setDefaultLabel(null);
                    setSearchInput('');
                    setShouldFocusTextInput(false);
                    dialogState.close();
                }}
                onOpenList={() => {
                    setSearchInput(defaultLabel.name);
                    setShouldFocusTextInput(true);
                    dialogState.open();
                }}
            />
        </div>
    );
};
