// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button } from '@geti-ui/ui';

interface AddSinkButtonProps {
    isPending: boolean;
    isDisabled: boolean;
}

export const AddSinkButton = ({ isPending, isDisabled }: AddSinkButtonProps) => {
    const { t } = useTranslation();

    return (
        <Button type='submit' isPending={isPending} isDisabled={isDisabled}>
            {t('common.actions.addAndUse')}
        </Button>
    );
};
