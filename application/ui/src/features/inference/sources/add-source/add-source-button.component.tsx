// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button } from '@geti-ui/ui';

interface AddSourceButtonProps {
    isPending: boolean;
    isDisabled: boolean;
}

export const AddSourceButton = ({ isPending, isDisabled }: AddSourceButtonProps) => {
    const { t } = useTranslation();

    return (
        <Button type='submit' isDisabled={isDisabled} isPending={isPending} alignSelf={'start'}>
            {t('common.actions.addAndUse')}
        </Button>
    );
};
