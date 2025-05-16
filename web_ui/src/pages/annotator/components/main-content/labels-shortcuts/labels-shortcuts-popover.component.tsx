// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useRef } from 'react';

import { Flex, Text, View } from '@adobe/react-spectrum';
import { CustomPopover } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { ChevronDownLight } from '../../../../../assets/icons';
import { Label } from '../../../../../core/labels/label.interface';
import { TaskLabelTreeSearch } from '../../../../../shared/components/task-label-tree-search/task-label-tree-search.component';
import { onEscape } from '../../../../../shared/utils';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { LabelShortcutButton } from './label-shortcut-item/label-shortcut-button.component';
import { PinLabelButton } from './pin-label-button.component';
import { UnpinLabelButton } from './unpin-label-button.component';

interface LabelShorcutPopoverProps {
    pinnedLabelsIds: string[];
    onLabelClick: (label: Label) => void;
    setPinnedLabelsIds: Dispatch<SetStateAction<string[]>>;
}

export const LabelsShortcutsPopover = ({
    pinnedLabelsIds,
    onLabelClick,
    setPinnedLabelsIds,
}: LabelShorcutPopoverProps) => {
    const triggerRef = useRef(null);
    const { tasks, selectedTask } = useTask();
    const labelPopoverState = useOverlayTriggerState({});

    const isPinned = (label: Label): boolean => pinnedLabelsIds.some((currentId) => label.id === currentId);

    const pinLabel = (labelId: string): void => {
        setPinnedLabelsIds([...pinnedLabelsIds, labelId]);
    };

    const unPinLabel = (labelId: string): void => {
        setPinnedLabelsIds(pinnedLabelsIds.filter((id) => labelId !== id));
    };

    return (
        <>
            <LabelShortcutButton onPress={labelPopoverState.toggle} ref={triggerRef}>
                <Flex direction={'row-reverse'} alignItems={'center'}>
                    <Text>More</Text>
                    <ChevronDownLight aria-label={'more-icon'} id={'more-icon'} />
                </Flex>
            </LabelShortcutButton>

            <CustomPopover
                ref={triggerRef}
                state={labelPopoverState}
                placement={'bottom right'}
                UNSAFE_style={{ border: 'none' }}
            >
                <View padding='size-100' width={'size-4600'} height={'31.2rem'}>
                    <TaskLabelTreeSearch
                        tasks={tasks}
                        selectedTask={selectedTask}
                        onClick={onLabelClick}
                        textFieldProps={{
                            onKeyDown: onEscape(labelPopoverState.close),
                        }}
                        suffix={(label, { isHovered }) => (
                            <View marginStart={'auto'}>
                                {isPinned(label) ? (
                                    <UnpinLabelButton unPinLabel={unPinLabel} labelId={label.id} />
                                ) : isHovered ? (
                                    <PinLabelButton pinLabel={pinLabel} labelId={label.id} />
                                ) : (
                                    <View width='size-400' height='size-225' />
                                )}
                            </View>
                        )}
                    />
                </View>
            </CustomPopover>
        </>
    );
};
