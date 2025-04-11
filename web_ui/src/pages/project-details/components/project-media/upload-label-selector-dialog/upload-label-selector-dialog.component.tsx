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

import { useEffect, useState } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { recursivelyAddLabel, recursivelyRemoveLabels } from '../../../../../core/labels/label-resolver';
import { Label } from '../../../../../core/labels/label.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { Button } from '../../../../../shared/components/button/button.component';
import { Checkbox } from '../../../../../shared/components/checkbox/checkbox.component';
import { TaskLabelTreeSearch } from '../../../../../shared/components/task-label-tree-search/task-label-tree-search.component';
import { hasEqualId, isNotCropTask, runWhenTruthy } from '../../../../../shared/utils';

interface UploadLabelSelectorDialogProps {
    tasks: Task[];
    isActivated: boolean;
    onDismiss: () => void;
    onSkipAction: () => void;
    onCancelUpload: () => void;
    onPrimaryAction: (labels: ReadonlyArray<Label>) => void;
}

export const UploadLabelSelectorDialog = ({
    tasks,
    isActivated,
    onDismiss,
    onSkipAction,
    onCancelUpload,
    onPrimaryAction,
}: UploadLabelSelectorDialogProps): JSX.Element => {
    const filteredTask = tasks.filter(isNotCropTask);
    const labels = filteredTask.flatMap(({ labels: taskLabels }) => taskLabels);
    const [selectedLabels, setSelectedLabels] = useState<ReadonlyArray<Label>>([]);

    const hasSelectedLabels = !isEmpty(selectedLabels);

    const handleToggleLabel = runWhenTruthy((label: Label): void => {
        if (selectedLabels.some(hasEqualId(label.id))) {
            const newLabelTree = recursivelyRemoveLabels(selectedLabels, [label]);

            setSelectedLabels(newLabelTree);
        } else {
            const newLabelTree = recursivelyAddLabel(selectedLabels, label, labels);

            setSelectedLabels(newLabelTree);
        }
    });

    useEffect(() => {
        if (!isActivated) {
            setSelectedLabels([]);
        }
    }, [isActivated]);

    return (
        <DialogContainer onDismiss={onDismiss}>
            {isActivated && (
                <Dialog size='M' minWidth={{ base: '6000', L: '86rem' }} minHeight={'56rem'}>
                    <Heading>Assign a label to the uploaded images</Heading>
                    <Divider />
                    <ButtonGroup>
                        <Button
                            variant='secondary'
                            onPress={() => {
                                onCancelUpload();
                                onDismiss();
                            }}
                            data-testid='cancel-button-id'
                            id='cancel-button-id'
                        >
                            Cancel upload
                        </Button>
                        <Button
                            variant='secondary'
                            onPress={() => {
                                onSkipAction();
                                onDismiss();
                            }}
                            data-testid='skip-button-id'
                            id='skip-button-id'
                        >
                            Skip
                        </Button>
                        <Button
                            variant='accent'
                            isDisabled={!hasSelectedLabels}
                            onPress={() => {
                                onPrimaryAction(selectedLabels);
                                onDismiss();
                            }}
                            data-testid='accept-button-id'
                            id='accept-button-id'
                        >
                            Accept
                        </Button>
                    </ButtonGroup>
                    <Content>
                        <TaskLabelTreeSearch
                            selectedTask={null}
                            tasks={filteredTask}
                            onClick={handleToggleLabel}
                            prefix={(label) => (
                                <Checkbox
                                    aria-label={label.name}
                                    onChange={() => handleToggleLabel(label)}
                                    isSelected={selectedLabels.some(hasEqualId(label.id))}
                                />
                            )}
                            ResultWrapper={({ children }) => (
                                <View backgroundColor={'gray-50'} marginY='size-100'>
                                    {children}
                                </View>
                            )}
                        />
                    </Content>
                </Dialog>
            )}
        </DialogContainer>
    );
};
