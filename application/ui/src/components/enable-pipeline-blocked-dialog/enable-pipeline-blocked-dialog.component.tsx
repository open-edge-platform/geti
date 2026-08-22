// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AlertDialog, DialogContainer } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

type EnablePipelineBlockedDialogProps = {
    isOpen: boolean;
    onClose: () => void;
};

export const EnablePipelineBlockedDialog = ({ isOpen, onClose }: EnablePipelineBlockedDialogProps) => {
    const { t } = useTranslation();

    return (
        <DialogContainer onDismiss={onClose}>
            {isOpen && (
                <AlertDialog
                    title={t('inference.cannotEnableTitle')}
                    primaryActionLabel={t('common.close')}
                    variant={'warning'}
                    onPrimaryAction={onClose}
                >
                    {t('inference.cannotEnableText')}
                </AlertDialog>
            )}
        </DialogContainer>
    );
};
