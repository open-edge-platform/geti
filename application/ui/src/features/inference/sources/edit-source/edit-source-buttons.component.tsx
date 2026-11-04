// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button, ButtonGroup, Divider } from '@geti-ui/ui';

interface EditSourceButtonsProps {
    isPending: boolean;
    isConnected: boolean;
    onSave: () => void;
    onSaveAndConnect: () => void;
}

export const EditSourceButtons = ({ isPending, isConnected, onSave, onSaveAndConnect }: EditSourceButtonsProps) => {
    const { t } = useTranslation();

    return (
        <>
            <Divider size='S' marginY={'size-200'} />

            <ButtonGroup marginTop={'0px'}>
                <Button
                    type='submit'
                    isDisabled={isPending}
                    UNSAFE_style={{ maxWidth: 'fit-content' }}
                    onPress={onSave}
                >
                    {t('common.actions.save')}
                </Button>

                {!isConnected && (
                    <Button
                        type='submit'
                        isDisabled={isPending}
                        UNSAFE_style={{ maxWidth: 'fit-content' }}
                        onPress={onSaveAndConnect}
                    >
                        {t('common.actions.saveAndConnect')}
                    </Button>
                )}
            </ButtonGroup>
        </>
    );
};
