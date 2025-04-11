// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useRef } from 'react';

import { Flex, SpectrumActionButtonProps, View } from '@adobe/react-spectrum';
import Checkmark from '@spectrum-icons/workflow/Checkmark';
import { clsx } from 'clsx';
import isEmpty from 'lodash/isEmpty';
import { OverlayTriggerState, useOverlayTriggerState } from 'react-stately';

import { recursivelyAddLabel, recursivelyRemoveLabels } from '../../../core/labels/label-resolver';
import { Label } from '../../../core/labels/label.interface';
import { isAnomalyDomain } from '../../../core/projects/domains';
import { CustomPopover } from '../../../shared/components/custom-popover/custom-popover.component';
import { QuietActionButton } from '../../../shared/components/quiet-button/quiet-action-button.component';
import { TaskLabelTreeSearch } from '../../../shared/components/task-label-tree-search/task-label-tree-search.component';
import { hasEqualId } from '../../../shared/utils';
import { useTask } from '../../annotator/providers/task-provider/task-provider.component';
import { useProject } from '../../project-details/providers/project-provider/project-provider.component';
import { getForegroundColor, hexaToRGBA } from '../../utils';
import { isClassificationOrAnomaly } from '../util';

import classes from './camera-page.module.scss';

interface LabelSelectorProps extends Omit<SpectrumActionButtonProps, 'isQuiet'> {
    name: string;
    labelIds: string[];
    selectedLabels: Label[];
    triggerState?: OverlayTriggerState;
    onSelectLabel: (data: Label[]) => void;
}

export const LabelSelector = ({
    name,
    labelIds,
    isDisabled,
    triggerState,
    onSelectLabel,
    selectedLabels,
    ...buttonStyles
}: LabelSelectorProps): JSX.Element => {
    const triggerRef = useRef(null);

    const { tasks } = useTask();
    const { isSingleDomainProject } = useProject();

    const localState = useOverlayTriggerState({});
    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);

    const [selectedTask] = tasks.filter(isClassificationOrAnomaly);
    const labelSelectorState = triggerState ?? localState;
    const selectedLabel = selectedTask?.labels?.find(hasEqualId(labelIds.at(-1)));

    const handleLabelClick = (label: Label) => {
        if (selectedLabels.some(hasEqualId(label.id))) {
            // For anomaly projects we want to disallow empty choice.
            // So if the user presses the label that is selected, we do nothing.
            if (isAnomalyProject && label.id === selectedLabel?.id) {
                labelSelectorState.close();

                return;
            }

            onSelectLabel([...recursivelyRemoveLabels(selectedLabels, [label])]);
        } else {
            onSelectLabel([...recursivelyAddLabel(selectedLabels, label, selectedTask?.labels)]);
        }

        labelSelectorState.close();
    };

    return (
        <>
            <Flex>
                {isEmpty(selectedLabels) ? (
                    <QuietActionButton
                        ref={triggerRef}
                        {...buttonStyles}
                        id={'select-label-button-id'}
                        onPress={labelSelectorState.toggle}
                        isDisabled={isEmpty(selectedTask?.labels) || isDisabled}
                        UNSAFE_className={[classes.labelSelectorButton, buttonStyles.UNSAFE_className].join(' ')}
                        UNSAFE_style={{
                            ...buttonStyles.UNSAFE_style,
                            color: 'var(--spectrum-actionbutton-quiet-text-color)',
                            background: 'var(--spectrum-global-color-gray-50)',
                        }}
                    >
                        {name}
                    </QuietActionButton>
                ) : (
                    selectedLabels.map((label: Label) => {
                        const { name: selectedLabelName, color } = label;
                        const selectedLabelButtonColor = getForegroundColor(
                            hexaToRGBA(color),
                            'var(--spectrum-global-color-gray-50)',
                            'var(--spectrum-global-color-gray-900)'
                        );

                        return (
                            <QuietActionButton
                                key={label.id}
                                id={`label-button-${label.id}-id`}
                                ref={triggerRef}
                                {...buttonStyles}
                                onPress={labelSelectorState.toggle}
                                isDisabled={isEmpty(selectedTask?.labels) || isDisabled}
                                UNSAFE_className={clsx(classes.labelSelectorButton, buttonStyles.UNSAFE_className)}
                                UNSAFE_style={{
                                    ...buttonStyles.UNSAFE_style,
                                    color: selectedLabelButtonColor,
                                    background: color,
                                }}
                            >
                                {selectedLabelName}
                            </QuietActionButton>
                        );
                    })
                )}
            </Flex>

            <CustomPopover
                ref={triggerRef}
                state={labelSelectorState}
                placement={'bottom left'}
                UNSAFE_style={{ border: 'none' }}
            >
                <View padding={'size-100'} width={'size-4600'} maxHeight={'size-3600'} overflow={'auto'}>
                    <TaskLabelTreeSearch
                        tasks={tasks}
                        selectedTask={selectedTask}
                        includesEmptyLabels={false}
                        onClick={handleLabelClick}
                        suffix={(label) =>
                            labelIds.includes(label.id) && (
                                <Checkmark
                                    size='S'
                                    UNSAFE_style={{ color: 'var(--spectrum-alias-icon-color-selected)' }}
                                />
                            )
                        }
                    />
                </View>
            </CustomPopover>
        </>
    );
};
