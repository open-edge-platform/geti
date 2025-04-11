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

import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import {
    GenerateOnboardingTokenParams,
    GenerateOnboardingTokenResponse,
} from '../services/onboarding-service.interface';

export const useGenerateOnboardingTokenMutation = () => {
    const { onboardingService } = useApplicationServices();

    const { addNotification } = useNotification();

    return useMutation<GenerateOnboardingTokenResponse, AxiosError, GenerateOnboardingTokenParams>({
        mutationFn: onboardingService.generateToken,
        onError: (error) => {
            addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
        },
    });
};
