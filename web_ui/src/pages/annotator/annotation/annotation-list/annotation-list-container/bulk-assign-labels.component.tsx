// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { QuietToggleButton } from '@shared/components/quiet-button/quiet-toggle-button.component';
import { TaskLabelTreeSearchPopover } from '@shared/components/task-label-tree-search/task-label-tree-search-popover.component';
import { getIds, hasEqualId, runWhenTruthy } from '@shared/utils';

import { Edit } from '../../../../../assets/icons';
import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { SelectionIndicator } from '../../../components/labels/label-search/selection-indicator.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useTask } from '../../../providers/task-provider/task-provider.component';

interface BulkAssignLabelProps {
    selectedAnnotations: ReadonlyArray<Annotation>;
    annotationToolContext: AnnotationToolContext;
    isDisabled: boolean;
}

export const BulkAssignLabel = ({ selectedAnnotations, annotationToolContext, isDisabled }: BulkAssignLabelProps) => {
    const [isOpened, setIsOpened] = useState(false);
    const { tasks, selectedTask } = useTask();

    const { addLabel, removeLabels } = annotationToolContext.scene;

    const labelIsAssignedToEveryAnnotation = (label: Label) => {
        return selectedAnnotations.every(({ labels }) => labels.some(hasEqualId(label.id)));
    };

    const onToggleLabel = runWhenTruthy((label: Label) => {
        const annotationIds = getIds([...selectedAnnotations]);

        if (labelIsAssignedToEveryAnnotation(label)) {
            removeLabels([label], annotationIds);
        } else {
            addLabel(label, annotationIds);
        }

        setIsOpened(false);
    });

    return (
        <View position='relative'>
            <QuietToggleButton
                isSelected={isOpened}
                isDisabled={isDisabled}
                onPress={() => setIsOpened(true)}
                id={'annotations-list-assign-label'}
                data-testid={'annotations-list-assign-label'}
                aria-label='Assign label to selected annotations'
            >
                <Edit />
            </QuietToggleButton>
            {isOpened && (
                <View
                    position='absolute'
                    marginTop='size-50'
                    width={{ base: 'size-2000', L: 'size-3000' }}
                    left={{ base: 'calc(size-800 * -1)', L: 'calc(size-1250 * -1)' }}
                    zIndex={15}
                >
                    <TaskLabelTreeSearchPopover
                        isFocus
                        tasks={tasks}
                        id={'bulk-anotations'}
                        selectedTask={selectedTask}
                        onClick={onToggleLabel}
                        onClose={() => setIsOpened(false)}
                        textFieldProps={{
                            placeholder: 'Select label',
                            'aria-label': 'Select label',
                        }}
                        suffix={(label, state) => {
                            return (
                                <Flex marginStart={'auto'} alignItems={'center'}>
                                    <SelectionIndicator
                                        isHovered={state.isHovered}
                                        isSelected={labelIsAssignedToEveryAnnotation(label)}
                                    />
                                </Flex>
                            );
                        }}
                    />
                </View>
            )}
        </View>
    );
};
