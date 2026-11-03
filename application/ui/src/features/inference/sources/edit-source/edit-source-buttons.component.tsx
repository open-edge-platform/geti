// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button, ButtonGroup, Divider } from '@geti-ui/ui';

interface EditSourceButtonsProps {
    isPending: boolean;
    isDisabled: boolean;
    isConnected: boolean;
    onSave: () => void;
    onSaveAndConnect: () => void;
}

export const EditSourceButtons = ({
    isPending,
    isDisabled,
    isConnected,
    onSave,
    onSaveAndConnect,
}: EditSourceButtonsProps) => {
    const { t } = useTranslation();

    return (
        <>
            <Divider size='S' marginY={'size-200'} />

            <ButtonGroup marginTop={0}>
                <Button type='submit' isDisabled={isDisabled} isPending={isPending} onPress={onSave}>
                    {t('common.actions.save')}
                </Button>

                {!isConnected && (
                    <Button type='submit' isDisabled={isDisabled} isPending={isPending} onPress={onSaveAndConnect}>
                        {t('common.actions.saveAndConnect')}
                    </Button>
                )}
            </ButtonGroup>
        </>
    );
};
