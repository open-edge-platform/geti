// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode, useLayoutEffect, useMemo, useRef } from 'react';

import {
    DefaultOptions,
    QueryCache,
    QueryClient,
    QueryClientProvider as TanstackQueryClientProvider,
} from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import get from 'lodash/get';

import { getErrorMessage } from '../../core/services/utils';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';

const SERVER_IS_UNAVAILABLE_STATUS_CODES = [StatusCodes.SERVICE_UNAVAILABLE, StatusCodes.TOO_MANY_REQUESTS];

export const QueryClientProvider = ({
    children,
    defaultQueryOptions,
}: {
    children: ReactNode;
    defaultQueryOptions?: DefaultOptions;
}) => {
    const { addNotification } = useNotification();

    // We want to make sure that query cache always uses the latest notification handler,
    // but we don't want to reset the cache every time this happens so we keep a ref instead
    const notify = useRef(addNotification);
    useLayoutEffect(() => {
        notify.current = addNotification;
    }, [addNotification]);

    const queryClient = useMemo(() => {
        const queryCache = new QueryCache({
            onError: (error, query) => {
                if (isAxiosError(error) && query.meta && 'notifyOnError' in query.meta) {
                    const message = query.meta.errorMessage;
                    if (query.meta.notifyOnError === true) {
                        notify.current({
                            message: typeof message === 'string' ? message : getErrorMessage(error),
                            type: NOTIFICATION_TYPE.ERROR,
                        });
                    }
                }

                if (query.meta && 'disableGlobalErrorHandling' in query.meta) {
                    if (query.meta.disableGlobalErrorHandling === true) {
                        return;
                    }
                }

                if (isAxiosError(error)) {
                    const statusCode: number | undefined = get(error, 'response.status');

                    if (statusCode && SERVER_IS_UNAVAILABLE_STATUS_CODES.includes(statusCode)) {
                        localStorage.setItem(LOCAL_STORAGE_KEYS.SERVICE_UNAVAILABLE, 'true');
                        window.dispatchEvent(new Event('storage'));

                        return Promise.reject(error);
                    }

                    if (statusCode === StatusCodes.FORBIDDEN) {
                        localStorage.setItem(LOCAL_STORAGE_KEYS.PROJECT_ACCESS_DENIED, 'true');
                        window.dispatchEvent(new Event('storage'));
                    }
                }
            },
        });

        return new QueryClient({
            defaultOptions: {
                queries: {
                    refetchIntervalInBackground: false,
                    refetchOnWindowFocus: false,
                },
                ...defaultQueryOptions,
            },
            queryCache,
        });
    }, [defaultQueryOptions]);

    return (
        <TanstackQueryClientProvider client={queryClient}>
            {children}

            {process.env.REACT_APP_REACT_QUERY_TOOL === 'true' && <ReactQueryDevtools initialIsOpen={false} />}
        </TanstackQueryClientProvider>
    );
};
