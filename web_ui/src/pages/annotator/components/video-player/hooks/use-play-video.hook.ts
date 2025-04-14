// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useEffect, useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import {
    PredictionCache,
    PredictionResult,
} from '../../../../../core/annotations/services/prediction-service.interface';
import { isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { useInterval } from '../../../../../hooks/use-interval/use-interval.hook';
import { loadImage } from '../../../../../shared/utils';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { useConstructVideoFrame } from './use-construct-video-frame.hook';

const useLoadAndSelectVideoFrameMutation = (
    selectVideoFrame: (frameNumber: number, showConfirmation?: boolean) => void
) => {
    const { annotationService } = useApplicationServices();
    const { project } = useProject();
    const { datasetIdentifier } = useDataset();
    const { selectedTask } = useTask();

    const queryClient = useQueryClient();

    // Prefetch the videoFrame's image, annotations and predictions so that when we select
    // it the user does not see a loading indicator
    return useMutation({
        mutationFn: async (videoFrame: VideoFrame) => {
            const [image, annotations] = await Promise.all([
                loadImage(videoFrame.src),
                annotationService.getAnnotations(datasetIdentifier, project.labels, videoFrame),
            ]);

            queryClient.setQueryData<HTMLImageElement>(
                QUERY_KEYS.SELECTED_MEDIA_ITEM.IMAGE(videoFrame.identifier),
                () => image
            );
            queryClient.setQueryData<ReadonlyArray<Annotation> | undefined>(
                QUERY_KEYS.SELECTED_MEDIA_ITEM.ANNOTATIONS(videoFrame.identifier),
                () => annotations
            );

            // Set the predictions for the current task
            queryClient.setQueryData<PredictionResult>(
                QUERY_KEYS.SELECTED_MEDIA_ITEM.PREDICTIONS(
                    videoFrame.identifier,
                    'videoFrame',
                    PredictionCache.AUTO,
                    selectedTask?.id
                ),
                () => ({ annotations: [], maps: [] })
            );
        },
        onSuccess: (_, videoFrame: VideoFrame) => {
            selectVideoFrame(videoFrame.identifier.frameNumber, false);
        },
    });
};

const usePlayIndexFrameNumber = (videoFrame: VideoFrame | undefined, isPlaying: boolean, step: number) => {
    const frameNumber = videoFrame?.identifier?.frameNumber ?? 0;
    const [playIndexFrameNumber, setPlayIndexFrameNumber] = useState(frameNumber);

    // Update the playIndexFrameNumber if the user manually changed the videoFrame
    useEffect(() => {
        if (!isPlaying) {
            const currentIndex = Math.round(frameNumber / step);

            if (currentIndex !== playIndexFrameNumber) {
                setPlayIndexFrameNumber(currentIndex > 0 ? currentIndex : 0);
            }
        }
    }, [isPlaying, frameNumber, step, playIndexFrameNumber]);

    return [playIndexFrameNumber, setPlayIndexFrameNumber] as const;
};

const getVideoPlayingTimeout = (isPlaying: boolean, step: number, fps: number) => {
    if (!isPlaying) {
        return null;
    }

    // When the user plays the video we want to simulate the same duration as the video itself,
    // therefore we try to set the timeout so that: video duration in ms = frames / step * timeout
    const timeout = Math.max(Math.min((1000 * step) / fps, 1000), 100);

    return timeout;
};

export const usePlayVideo = (
    videoFrame: VideoFrame | undefined,
    step: number,
    selectFrame: (frameNumber: number, showConfirmation?: boolean) => void
): [boolean, Dispatch<SetStateAction<boolean>>] => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [playIndexFramenumber, setPlayIndexFramenumber] = usePlayIndexFrameNumber(videoFrame, isPlaying, step);

    const loadAndSelectVideoFrameMutation = useLoadAndSelectVideoFrameMutation(selectFrame);

    // Try to play the video with a fixed fps by preloading videoFrames
    const timeout = getVideoPlayingTimeout(isPlaying, step, videoFrame?.metadata?.fps ?? 1);

    const constructVideoFrame = useConstructVideoFrame(videoFrame);

    useInterval(async () => {
        if (!isPlaying || videoFrame === undefined || !isVideoFrame(videoFrame)) {
            return;
        }

        const totalSegments = Math.max(Math.ceil(videoFrame.metadata.frames / step), 0);
        const nextIndex = playIndexFramenumber + 1 < totalSegments ? playIndexFramenumber + 1 : 0;
        const nextVideoFrame = Math.min(videoFrame.metadata.frames, nextIndex * step);

        // Skip preloading a videoFrame if another one is being loaded
        if (
            (loadAndSelectVideoFrameMutation.isIdle || loadAndSelectVideoFrameMutation.isSuccess) &&
            nextVideoFrame !== videoFrame.identifier.frameNumber
        ) {
            const newVideoFrame = constructVideoFrame(nextVideoFrame);

            if (newVideoFrame) {
                await loadAndSelectVideoFrameMutation.mutate(newVideoFrame, {
                    onSuccess: () => {
                        setPlayIndexFramenumber(nextIndex);
                    },
                });
            }
        }
    }, timeout);

    return [isPlaying, setIsPlaying];
};
