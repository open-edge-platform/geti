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
