// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect } from 'react';

import { useLocalStorage } from 'usehooks-ts';

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { usePreviousSignIn } from '../../hooks/use-previous-sign-in.hook';
import { LOCAL_STORAGE_KEYS } from '../../local-storage-keys';

export const LastLoginNotification = (): JSX.Element => {
    const isSaaS = useIsSaasEnv();
    const { addToastNotification } = useNotification();
    const { lastLoginDate, userId } = usePreviousSignIn();
    const [lastLoginInfo, setLastLoginInfo] = useLocalStorage<string>(LOCAL_STORAGE_KEYS.LAST_LOGIN_INFO, '');

    useEffect(() => {
        if (isSaaS) {
            if (`${userId}-${lastLoginDate}` !== lastLoginInfo && lastLoginDate) {
                addToastNotification({
                    message: `Your previous sign-in was \n${lastLoginDate}`,
                    type: NOTIFICATION_TYPE.DEFAULT,
                    placement: 'top-right',
                });

                setLastLoginInfo(`${userId}-${lastLoginDate}`);
            }
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isSaaS, lastLoginDate, lastLoginInfo, userId]);

    return <></>;
};
