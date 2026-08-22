// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AlertDialog, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

type AlertDialogContentProps = {
    itemsIds: string[];
    onPrimaryAction: () => void;
};

export const AlertDialogContent = ({ itemsIds, onPrimaryAction }: AlertDialogContentProps) => {
    const { t } = useTranslation();

    return (
        <AlertDialog
            maxHeight={'size-6000'}
            title={t('dataset.deleteItemsTitle')}
            variant='destructive'
            primaryActionLabel={t('dataset.confirmLabel')}
            secondaryActionLabel={t('common.cancel')}
            onPrimaryAction={onPrimaryAction}
            autoFocusButton='primary'
        >
            <Text>{t('dataset.deleteItemsConfirmation', { count: itemsIds.length })}</Text>
        </AlertDialog>
    );
};
