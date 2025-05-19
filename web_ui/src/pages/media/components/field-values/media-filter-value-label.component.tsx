// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeyboardEvent, useRef, useState } from 'react';

import { CustomPopover, TextArea, View } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isEmpty } from 'lodash-es';

import { Label } from '../../../../core/labels/label.interface';
import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { TaskLabelTreeContainer } from '../../../../shared/components/task-label-tree-search/task-label-tree-container.component';
import { useFilteredTaskMetadata } from '../../../../shared/components/task-label-tree-search/use-filtered-task-metadata.hook';
import { getIds, hasDifferentId, isNotCropTask, onEscape } from '../../../../shared/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import {
    concatByProperty,
    deleteLastComa,
    findLabelsById,
    getLowercaseTrimmedText,
    hasLabelsDifference,
    isKeyboardDelete,
} from '../../utils';

interface MediaFilterValueLabelProps {
    isDisabled?: boolean;
    value: string | string[];
    onSelectionChange: (key: SearchRuleValue) => void;
}

const getInitLabelsById = (value: string | string[], labels: Label[]): Label[] => {
    const names = Array.isArray(value) ? value : [value];

    return findLabelsById(names, labels);
};

export const MediaFilterValueLabel = ({
    value = '',
    isDisabled = false,
    onSelectionChange,
}: MediaFilterValueLabelProps): JSX.Element => {
    const {
        project: { labels, tasks },
    } = useProject();

    const triggerRef = useRef(null);
    const savedLabels = useRef<Label[]>(getInitLabelsById(value, labels));
    const [inputValue, setInputValue] = useState(() => concatByProperty(getInitLabelsById(value, labels), 'name'));
    const [searchInput, setSearchInput] = useState('');

    const dialogState = useOverlayTriggerState({});
    const filteredTask = tasks.filter(isNotCropTask);
    const selectedTask = filteredTask.length > 1 ? null : filteredTask[0];

    const setInputValueAndSelectionChange = (newLabels: Label[], callOnSelection = true) => {
        savedLabels.current = newLabels;
        setSearchInput('');
        setInputValue(concatByProperty(newLabels, 'name'));
        callOnSelection && onSelectionChange(getIds(newLabels));
    };

    const isLabelNameValid = (names: string) => {
        const splitNames = getLowercaseTrimmedText(deleteLastComa(names));
        const labelNames = labels.map(({ name }) => name.toLowerCase());

        return !isEmpty(splitNames) && splitNames.every((name) => labelNames.includes(name));
    };

    const treeItemClickHandler = (label: Label): void => {
        const isNewLabel = savedLabels.current.every(hasDifferentId(label.id));
        if (isNewLabel) {
            setInputValueAndSelectionChange([...savedLabels.current, label]);
            dialogState.close();
        }
    };

    const onKeyUp = (event: KeyboardEvent) => {
        const textValue = (event.target as HTMLInputElement).value;
        const searchNames = getLowercaseTrimmedText(textValue);

        const newLabels = labels.filter(({ name }) => searchNames.includes(name.toLowerCase()));
        const lastSearchName = searchNames.at(-1) ?? '';

        setSearchInput(lastSearchName);

        if (isKeyboardDelete(event) && hasLabelsDifference(savedLabels.current, newLabels)) {
            setInputValueAndSelectionChange(newLabels);
        }
    };

    const results = useFilteredTaskMetadata({
        input: searchInput,
        tasks: filteredTask,
        selectedTask,
    });

    return (
        <div style={{ position: 'relative' }}>
            <TextArea
                isQuiet
                width={'auto'}
                ref={triggerRef}
                value={inputValue}
                onFocus={() => {
                    dialogState.open();
                }}
                onKeyUp={onKeyUp}
                onKeyDown={onEscape(dialogState.close)}
                isDisabled={isDisabled}
                id='media-filter-label'
                aria-label={'media-filter-label'}
                validationState={isLabelNameValid(inputValue) ? 'valid' : 'invalid'}
                onChange={(currentValue) => {
                    setInputValue(currentValue);
                    dialogState.open();
                }}
            />

            <CustomPopover state={dialogState} ref={triggerRef}>
                <View padding={'size-100'} width={'size-4600'} maxHeight={'31.2rem'} overflow={'hidden auto'}>
                    <TaskLabelTreeContainer
                        ariaLabel='media filter label results'
                        tasksMetadata={results}
                        onClick={treeItemClickHandler}
                    />
                </View>
            </CustomPopover>
        </div>
    );
};
