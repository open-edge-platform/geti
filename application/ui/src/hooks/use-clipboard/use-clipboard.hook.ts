// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isEmpty } from 'lodash-es';

import { toast } from '../../components/toast/toast.component';
import { i18n } from '../../i18n/config';

export const useClipboard = () => {
    const copy = (
        text: string,
        successMessage = i18n.t('common.copiedSuccessfully'),
        errorMessage = i18n.t('common.copyFailed')
    ) =>
        navigator.clipboard
            .writeText(text)
            .then(() => !isEmpty(successMessage) && toast({ message: successMessage, type: 'info' }))
            .catch(() => toast({ message: errorMessage, type: 'error' }));

    return { copy };
};
