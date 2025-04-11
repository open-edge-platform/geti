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

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useFeatureFlags } from '../../feature-flags/hooks/use-feature-flags.hook';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { StatusProps } from '../status.interface';
import {
    isBelowLowFreeDiskSpace,
    isBelowTooLowFreeDiskSpace,
    LOW_FREE_DISK_SPACE_MESSAGE,
    TOO_LOW_FREE_DISK_SPACE_MESSAGE,
} from './utils';

export const useStatus = (): UseQueryResult<StatusProps, AxiosError> => {
    const { addNotification } = useNotification();
    const { organizationId } = useOrganizationIdentifier();
    const { FEATURE_FLAG_STORAGE_SIZE_COMPUTATION } = useFeatureFlags();

    const [isTooLowOpenOnce, setIsTooLowOpenOnce] = useState(true);
    const [isLowOpenOnce, setIsLowOpenOnce] = useState(true);
    const { statusService: service } = useApplicationServices();

    const statusQuery = useQuery<StatusProps, AxiosError>({
        queryKey: QUERY_KEYS.STATUS_KEY(),
        queryFn: () => {
            return service.getStatus(organizationId);
        },
        notifyOnChangeProps: ['data', 'error'],
    });

    useEffect(() => {
        if (!statusQuery.isSuccess) {
            return;
        }

        if (!FEATURE_FLAG_STORAGE_SIZE_COMPUTATION) {
            return;
        }

        if (isBelowTooLowFreeDiskSpace(statusQuery.data.freeSpace)) {
            if (isTooLowOpenOnce) {
                addNotification({
                    message: TOO_LOW_FREE_DISK_SPACE_MESSAGE,
                    type: NOTIFICATION_TYPE.ERROR,
                    dismiss: { duration: 0 },
                });
                setIsTooLowOpenOnce(false);
            }

            return;
        }

        if (isBelowLowFreeDiskSpace(statusQuery.data.freeSpace)) {
            if (isLowOpenOnce) {
                addNotification({
                    message: LOW_FREE_DISK_SPACE_MESSAGE,
                    type: NOTIFICATION_TYPE.WARNING,
                    dismiss: { duration: 0 },
                });
                setIsLowOpenOnce(false);
            }

            return;
        }
    }, [
        statusQuery.isSuccess,
        statusQuery.data,
        FEATURE_FLAG_STORAGE_SIZE_COMPUTATION,
        addNotification,
        setIsLowOpenOnce,
        isLowOpenOnce,
        isTooLowOpenOnce,
    ]);

    return statusQuery;
};
