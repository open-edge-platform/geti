// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useQuery } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { PredictionResult } from '../../../../../core/annotations/services/prediction-service.interface';
import { isImage } from '../../../../../core/media/image.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideoFrame } from '../../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { isNonEmptyString } from '../../../../../shared/utils';
import { useAnnotationsQuery } from '../../../../annotator/providers/selected-media-item-provider/use-annotations-query.hook';
import { useLoadImageQuery } from '../../../../annotator/providers/selected-media-item-provider/use-load-image-query.hook';
import { useProject } from '../../../providers/project-provider/project-provider.component';

const getTestResult = (media: MediaItem, testMediaItem: TestMediaItem) => {
    if (isImage(media) && testMediaItem.type === 'image') {
        if (media.identifier.imageId === testMediaItem.media.identifier.imageId) {
            return testMediaItem.testResult;
        }
    }

    if (isVideoFrame(media) && testMediaItem.type === 'video_frame') {
        if (
            media.identifier.videoId === testMediaItem.media.identifier.videoId &&
            media.identifier.frameNumber === testMediaItem.media.identifier.frameNumber
        ) {
            return testMediaItem.testResult;
        }
    }

    if (testMediaItem.type === 'video' && isVideoFrame(media)) {
        const testResult = testMediaItem.filteredFrames.find((result) => {
            return result.frameIndex === media.identifier.frameNumber;
        });

        return testResult;
    }

    return undefined;
};

export const useTestResultsQuery = (
    datasetIdentifier: DatasetIdentifier,
    mediaItem: MediaItem,
    testMediaItem: TestMediaItem,
    testId: string
) => {
    const {
        project: { labels },
    } = useProject();

    const projectIdentifier = useProjectIdentifier();

    const imageQuery = useLoadImageQuery(mediaItem);
    const testResult = getTestResult(mediaItem, testMediaItem);
    const { annotationService, inferenceService } = useApplicationServices();

    const annotationsQuery = useAnnotationsQuery({
        annotationService,
        coreLabels: labels,
        datasetIdentifier,
        mediaItem,
        annotationId: testResult?.annotationId,
    });

    const predictionsQuery = useQuery<PredictionResult, AxiosError>({
        queryKey: QUERY_KEYS.TEST_PREDICTIONS(projectIdentifier, testId, String(testResult?.predictionId)),
        queryFn: () =>
            Promise.allSettled([
                inferenceService.getTestPredictions(
                    datasetIdentifier,
                    labels,
                    testId,
                    String(testResult?.predictionId)
                ),
                inferenceService.getExplanations(datasetIdentifier, mediaItem),
            ]).then(([predictions, explanations]) => {
                // @ts-expect-error PromiseSettledResult type is not exported
                // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled
                return { annotations: predictions.value ?? [], maps: explanations.value ?? [] };
            }),
        enabled: isNonEmptyString(testResult?.predictionId),
    });

    return {
        imageQuery,
        annotationsQuery,
        predictionsQuery,
        testResult,
    };
};
