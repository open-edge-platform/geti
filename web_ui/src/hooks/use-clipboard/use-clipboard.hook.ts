// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';

import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';

export const useClipboard = () => {
    const { addNotification } = useNotification();

    const copy = (text: string, successMessage = 'Copied Successfully', errorMessage = 'Copy failed') =>
        navigator.clipboard
            .writeText(text)
            .then(
                () =>
                    !isEmpty(successMessage) &&
                    addNotification({ message: successMessage, type: NOTIFICATION_TYPE.INFO })
            )
            .catch(() => addNotification({ message: errorMessage, type: NOTIFICATION_TYPE.ERROR }));

    return { copy };
};
