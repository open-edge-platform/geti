// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button, ButtonGroup, Divider } from '@geti-ui/ui';

interface EditSinkButtonsProps {
    isPending: boolean;
    isDisabled: boolean;
    isConnected: boolean;
    onSave: () => void;
    onSaveAndConnect: () => void;
}

export const EditSinkButtons = ({
    isPending,
    isDisabled,
    isConnected,
    onSave,
    onSaveAndConnect,
}: EditSinkButtonsProps) => {
    const { t } = useTranslation();

    return (
        <>
            <Divider size='S' marginY={'size-200'} />

            <ButtonGroup marginTop={0}>
                <Button type='submit' isPending={isPending} isDisabled={isDisabled} onPress={onSave}>
                    {t('common.actions.save')}
                </Button>

                {!isConnected && (
                    <Button type='submit' isPending={isPending} isDisabled={isDisabled} onPress={onSaveAndConnect}>
                        {t('common.actions.saveAndConnect')}
                    </Button>
                )}
            </ButtonGroup>
        </>
    );
};
