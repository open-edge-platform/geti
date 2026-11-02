// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button } from '@geti-ui/ui';

interface AddSourceButtonProps {
    isPending: boolean;
}

export const AddSourceButton = ({ isPending }: AddSourceButtonProps) => {
    const { t } = useTranslation();

    return (
        <Button type='submit' isDisabled={isPending} UNSAFE_style={{ maxWidth: 'fit-content' }}>
            {t('common.actions.addAndUse')}
        </Button>
    );
};
