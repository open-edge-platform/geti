// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useState } from 'react';

import { StatusCodes } from 'http-status-codes';
import { useErrorHandler } from 'react-error-boundary';

import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';
import { removeLocalStorageKey } from '../../shared/utils';

export const useStorage = () => {
    const errorHandler = useErrorHandler();
    const [isOpenDialogAccessDenied, setIsOpenDialogAccessDenied] = useState<boolean>(false);

    useEffect(() => {
        const listenerCallback = () => {
            if (localStorage.getItem(LOCAL_STORAGE_KEYS.UNAUTHORIZED) === 'true') {
                errorHandler({ message: StatusCodes.UNAUTHORIZED });
                removeLocalStorageKey(LOCAL_STORAGE_KEYS.UNAUTHORIZED);
            } else if (localStorage.getItem(LOCAL_STORAGE_KEYS.SERVICE_UNAVAILABLE) === 'true') {
                errorHandler({ message: StatusCodes.SERVICE_UNAVAILABLE });
                removeLocalStorageKey(LOCAL_STORAGE_KEYS.SERVICE_UNAVAILABLE);
            } else if (localStorage.getItem(LOCAL_STORAGE_KEYS.PROJECT_ACCESS_DENIED) === 'true') {
                setIsOpenDialogAccessDenied(true);
            }
        };

        window.addEventListener('storage', listenerCallback);

        return () => {
            window.removeEventListener('storage', listenerCallback);
        };
    }, [errorHandler]);

    return {
        isOpenDialogAccessDenied,
        handleClose: () => {
            setIsOpenDialogAccessDenied(false);
            removeLocalStorageKey(LOCAL_STORAGE_KEYS.PROJECT_ACCESS_DENIED);
        },
    };
};
