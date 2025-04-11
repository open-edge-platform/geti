// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
