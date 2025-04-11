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

import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import {
    ExplanationResult,
    InferenceResult,
} from '../../../../../core/annotations/services/inference-service.interface';
import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { getErrorMessageByStatusCode } from '../../../../../core/services/utils';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';

// If the user did not send an inference request recently then the service may be unavailable,
// starting up this service can take a while so we want to retry multiple times using exponential backoff
const RETRY_ATTEMPTS = 4;

interface UseQuickInferenceMutation {
    predictionMutation: UseMutationResult<
        InferenceResult,
        AxiosError,
        { projectIdentifier: ProjectIdentifier; file: File }
    >;
    explainMutation: UseMutationResult<
        ExplanationResult,
        AxiosError,
        { projectIdentifier: ProjectIdentifier; file: File }
    >;
}

const retryDelay = (attemptIndex: number) => Math.min(3000 * 2 ** attemptIndex, 30000);

export const useQuickInferenceMutation = (): UseQuickInferenceMutation => {
    const { inferenceService } = useApplicationServices();
    const { addNotification } = useNotification();
    const { project } = useProject();

    const onError = (error: AxiosError) => {
        const message = getErrorMessageByStatusCode(error);

        addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
    };

    const predictionMutation = useMutation({
        mutationFn: ({ projectIdentifier, file }: { projectIdentifier: ProjectIdentifier; file: File }) => {
            return inferenceService.getPredictionsForFile(projectIdentifier, project.labels, file);
        },
        onError,
        retry: RETRY_ATTEMPTS,
        retryDelay,
    });

    const explainMutation = useMutation({
        mutationFn: ({ projectIdentifier, file }: { projectIdentifier: ProjectIdentifier; file: File }) => {
            return inferenceService.getExplanationsForFile(projectIdentifier, file);
        },
        onError,
        retry: RETRY_ATTEMPTS,
        retryDelay,
    });

    return {
        predictionMutation,
        explainMutation,
    };
};
