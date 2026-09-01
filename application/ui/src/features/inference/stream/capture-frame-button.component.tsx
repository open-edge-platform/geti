// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from '@geti-ui/ui';
import { useCapturePipelineFrame, usePipeline, usePipelineHealth } from 'hooks/api/pipeline.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { toast } from '../../../components/toast/toast.component';
import { useWebRTCConnection } from './web-rtc-connection-provider';

export const CaptureFrameButton = () => {
    const projectId = useProjectIdentifier();
    const { data: pipeline } = usePipeline();
    const {
        data: pipelineHealth,
        isPending: isPipelineHealthPending,
        isError: isPipelineHealthError,
    } = usePipelineHealth();
    const { status: streamStatus } = useWebRTCConnection();
    const captureFrameMutation = useCapturePipelineFrame();

    const isPipelineRunning = pipeline.status === 'running';
    const isStreamConnected = streamStatus === 'connected';
    // The backend collects the *next* frame the source produces, so a source that ended
    // (e.g. a non-looping video file) or errored can never fulfil the request.
    const sourceStatus = pipelineHealth?.components?.source.status;
    const isSourceProducingFrames = isPipelineHealthError || sourceStatus === undefined || sourceStatus === 'ok';

    const isCaptureDisabled =
        isPipelineHealthPending ||
        !isPipelineRunning ||
        !isStreamConnected ||
        !isSourceProducingFrames ||
        captureFrameMutation.isPending;

    const handleCapture = () => {
        captureFrameMutation.mutate(
            { params: { path: { project_id: projectId } } },
            {
                onSuccess: () => {
                    toast({ type: 'success', message: 'Frame captured!' });
                },
            }
        );
    };

    return (
        <Button variant={'secondary'} onPress={handleCapture} isDisabled={isCaptureDisabled}>
            Capture frame
        </Button>
    );
};
