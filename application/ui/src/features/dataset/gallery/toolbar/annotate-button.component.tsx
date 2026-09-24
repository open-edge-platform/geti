// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useTranslation } from '@/i18n';
import { Button, DialogContainer, Item, Key, Menu, MenuTrigger } from '@geti-ui/ui';
import { ChevronDownSmall } from '@geti-ui/ui/icons';

import { BatchAnnotationDialog } from '../../../ai-assistant/batch/batch-annotation-dialog.component';

import classes from './annotate-button.module.scss';

interface AnnotateButtonProps {
    isDisabled?: boolean;
    onAnnotate: () => void;
    selectedMediaIds: string[];
    resolveAllMediaIds: () => Promise<string[] | null>;
}

export const AnnotateButton = ({
    isDisabled,
    onAnnotate,
    selectedMediaIds,
    resolveAllMediaIds,
}: AnnotateButtonProps) => {
    const { t } = useTranslation();
    const [isBatchDialogOpen, setIsBatchDialogOpen] = useState(false);

    const handleMenuAction = (key: Key) => {
        if (key === 'ai') setIsBatchDialogOpen(true);
    };

    return (
        <>
            <div className={classes.splitButton}>
                <Button margin={0} variant='primary' onPress={onAnnotate} isDisabled={isDisabled}>
                    {t('common.actions.annotate')}
                </Button>
                <MenuTrigger>
                    <Button
                        margin={0}
                        variant='primary'
                        aria-label='Annotate options'
                        isDisabled={isDisabled}
                        UNSAFE_className={classes.menuButton}
                    >
                        <ChevronDownSmall />
                    </Button>
                    <Menu onAction={handleMenuAction} aria-label='Annotate options menu'>
                        <Item key='ai'>Annotate with AI</Item>
                    </Menu>
                </MenuTrigger>
            </div>

            <DialogContainer onDismiss={() => setIsBatchDialogOpen(false)}>
                {isBatchDialogOpen && (
                    <BatchAnnotationDialog
                        selectedMediaIds={selectedMediaIds}
                        resolveAllMediaIds={resolveAllMediaIds}
                        onClose={() => setIsBatchDialogOpen(false)}
                    />
                )}
            </DialogContainer>
        </>
    );
};
