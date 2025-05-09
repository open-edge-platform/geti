// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { useLocalStorage } from 'usehooks-ts';

import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { usePreviousSignIn } from '../../shared/hooks/use-previous-sign-in.hook';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';

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
