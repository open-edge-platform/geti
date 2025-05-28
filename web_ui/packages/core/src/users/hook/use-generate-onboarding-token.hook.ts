// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../../../src/notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../src/notification/notification.component';
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
