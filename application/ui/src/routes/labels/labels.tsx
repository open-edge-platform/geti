// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { Label } from '@/api/types';
import { validateLabelHotkey, validateLabelName } from '@/components/label-fields/label-validation';
import { useTranslation } from '@/i18n';
import { ActionButton, AlertDialog, DialogContainer, Divider, Flex, Heading, Text, View } from '@geti-ui/ui';
import { Add } from '@geti-ui/ui/icons';
import { useProject } from 'hooks/api/project.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { useUpdateLabel } from '../../features/annotator/labels/api/use-update-label.hook';
import { LabelRow } from '../../features/annotator/labels/label-row/label-row.component';
import { NewLabelRow } from '../../features/annotator/labels/new-label-row/new-label-row.component';
import { convertHotkeyToOSFormat, TASK_HOTKEYS } from '../../shared/hotkeys-definition';
import { isNonEmptyString } from '../../shared/util';

export const Labels = () => {
    const { data: project } = useProject();
    const projectId = useProjectIdentifier();
    const { t } = useTranslation();
    const mutation = useUpdateLabel();
    const [isCreating, setIsCreating] = useState((project.task.labels ?? []).length === 0);
    const [labelToDelete, setLabelToDelete] = useState<Label | null>(null);
    const labels = project.task.labels ?? [];

    const validateName = (name: string, excludeId?: string) => validateLabelName(name, labels, t, excludeId);
    const validateHotkey = (hotkey: string, excludeId?: string) => {
        const labelHotkeys = labels
            .filter(({ id }) => id !== excludeId)
            .map(({ hotkey: value }) => (isNonEmptyString(value) ? convertHotkeyToOSFormat(value) : null))
            .filter((value): value is string => value !== null);

        return hotkey
            ? validateLabelHotkey(hotkey, [...labelHotkeys, ...Object.values(TASK_HOTKEYS[project.task.task_type])], t)
            : undefined;
    };

    const addLabel = (name: string, color: string, hotkey?: string) => {
        mutation.mutate({
            body: { labels_to_add: [{ name, color, hotkey: hotkey ?? null }] },
            params: { path: { project_id: projectId } },
        });
        setIsCreating(false);
    };

    const updateLabel = (
        labelId: string,
        updates: { name: string; color: string; hotkey: string | null | undefined }
    ) => {
        mutation.mutate({
            body: {
                labels_to_edit: [
                    { id: labelId, new_name: updates.name, new_color: updates.color, new_hotkey: updates.hotkey },
                ],
            },
            params: { path: { project_id: projectId } },
        });
    };

    const deleteLabel = () => {
        if (labelToDelete === null) return;
        mutation.mutate({
            body: { labels_to_remove: [{ id: labelToDelete.id }] },
            params: { path: { project_id: projectId } },
        });
        setLabelToDelete(null);
    };

    return (
        <View height='100%' padding='size-300' overflow='auto'>
            <Flex direction='column' gap='size-300' maxWidth='size-6000'>
                <Flex alignItems='center' justifyContent='space-between'>
                    <View>
                        <Heading margin={0}>Labels</Heading>
                        <Text>Edit the classes used for annotations and training in this project.</Text>
                    </View>
                    <ActionButton onPress={() => setIsCreating(true)} isDisabled={isCreating || mutation.isPending}>
                        <Add /> Add label
                    </ActionButton>
                </Flex>
                <Divider size='S' />

                {labels.length === 0 && !isCreating && (
                    <Text>No labels yet. Add one or use Auto-Label in Dataset.</Text>
                )}

                {labels.map((label) => (
                    <LabelRow
                        key={label.id}
                        label={label}
                        isSelected={false}
                        isPinned={false}
                        onSelect={() => undefined}
                        onTogglePin={() => undefined}
                        onDelete={setLabelToDelete}
                        onUpdate={updateLabel}
                        validateName={validateName}
                        validateHotkey={validateHotkey}
                        showSelection={false}
                        showPin={false}
                    />
                ))}

                {isCreating && (
                    <NewLabelRow
                        onSave={addLabel}
                        onCancel={() => setIsCreating(false)}
                        validateName={validateName}
                        validateHotkey={validateHotkey}
                    />
                )}
            </Flex>

            <DialogContainer onDismiss={() => setLabelToDelete(null)}>
                {labelToDelete !== null && (
                    <AlertDialog
                        title='Delete label'
                        variant='destructive'
                        primaryActionLabel='Delete'
                        cancelLabel='Cancel'
                        onPrimaryAction={deleteLabel}
                        onCancel={() => setLabelToDelete(null)}
                    >
                        Removing {labelToDelete.name} also removes its annotations from this dataset.
                    </AlertDialog>
                )}
            </DialogContainer>
        </View>
    );
};
