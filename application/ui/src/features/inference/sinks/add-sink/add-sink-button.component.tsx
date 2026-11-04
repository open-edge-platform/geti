// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button } from '@geti-ui/ui';

interface AddSinkButtonProps {
    isPending: boolean;
}

export const AddSinkButton = ({ isPending }: AddSinkButtonProps) => {
    const { t } = useTranslation();

    return (
        <Button type='submit' isPending={isPending}>
            {t('common.actions.addAndUse')}
        </Button>
    );
};
