// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { Label } from '@/api/types';
import { ActionButton, AlertDialog, DialogContainer, DialogTrigger, Text, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Add, Edit } from '@geti-ui/ui/icons';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { useTranslation } from 'react-i18next';

import { useLabels } from '../use-labels.hook';
import { LabelsEditor } from './labels-editor.component';

const POPOVER_OFFSET_ALIGNMENT = 8;

type LabelsEditorPopoverProps = {
    isClassification?: boolean;
    isMultiLabel?: boolean;
    hasLabels: boolean;
};

export const LabelsEditorPopover = ({
    isClassification = false,
    isMultiLabel = false,
    hasLabels,
}: LabelsEditorPopoverProps) => {
    const { deleteLabel } = useLabels({ isClassification, isMultiLabel });

    const popoverState = useOverlayTriggerState({});
    const deleteDialogState = useOverlayTriggerState({});
    const [labelToDelete, setLabelToDelete] = useState<Label | null>(null);

    const handleRequestDeleteLabel = (label: Label) => {
        setLabelToDelete(label);
        popoverState.close();
        deleteDialogState.open();
    };

    const handleConfirmDeleteLabel = () => {
        if (labelToDelete) {
            deleteDialogState.close();
            deleteLabel(labelToDelete.id);
            setLabelToDelete(null);
        }
    };

    const handleCancelDeleteLabel = () => {
        deleteDialogState.close();
        setLabelToDelete(null);
        popoverState.open();
    };

    const { t } = useTranslation();
    const triggerLabel = hasLabels ? t('annotator.editLabelsTrigger') : t('annotator.createLabelTrigger');

    return (
        <>
            <DialogTrigger
                type='popover'
                hideArrow
                isOpen={popoverState.isOpen}
                onOpenChange={popoverState.setOpen}
                placement='bottom end'
                offset={POPOVER_OFFSET_ALIGNMENT}
                crossOffset={POPOVER_OFFSET_ALIGNMENT}
            >
                <TooltipTrigger>
                    <ActionButton isQuiet aria-label={triggerLabel}>
                        {hasLabels ? (
                            <Edit />
                        ) : (
                            <>
                                <Add />
                                <Text>{t('annotator.createLabelTrigger')}</Text>
                            </>
                        )}
                    </ActionButton>
                    <Tooltip>{triggerLabel}</Tooltip>
                </TooltipTrigger>

                <LabelsEditor
                    isClassification={isClassification}
                    isMultiLabel={isMultiLabel}
                    onRequestDeleteLabel={handleRequestDeleteLabel}
                    autoCreateNewLabel={!hasLabels}
                />
            </DialogTrigger>

            <DialogContainer onDismiss={handleCancelDeleteLabel}>
                {deleteDialogState.isOpen && labelToDelete && (
                    <AlertDialog
                        title={t('annotator.deleteLabelTitle')}
                        variant={'destructive'}
                        primaryActionLabel={t('common.delete')}
                        cancelLabel={t('common.cancel')}
                        onPrimaryAction={handleConfirmDeleteLabel}
                        onCancel={handleCancelDeleteLabel}
                    >
                        {t('annotator.deleteLabelWarning', { name: labelToDelete.name })}
                    </AlertDialog>
                )}
            </DialogContainer>
        </>
    );
};
