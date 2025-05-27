// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { getErrorMessage } from '../../../../packages/core/src/services/utils';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
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
