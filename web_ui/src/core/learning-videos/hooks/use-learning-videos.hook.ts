// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useDocsUrl } from '../../../hooks/use-docs-url/use-docs-url.hook';
import { LearningVideo } from '../dtos/learning-video.interface';
import { LEARNING_VIDEOS } from './learning-videos';

interface UseLearningVideos {
    learningVideos: LearningVideo[];
}

export const useLearningVideos = (): UseLearningVideos => {
    const docsUrl = useDocsUrl();

    return {
        learningVideos: LEARNING_VIDEOS.map((video) => ({
            ...video,
            video: `${docsUrl}${video.video}`,
        })),
    };
};
