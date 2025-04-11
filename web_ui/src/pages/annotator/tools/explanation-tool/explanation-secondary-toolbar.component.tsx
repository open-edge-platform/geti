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

import isNil from 'lodash/isNil';

import { isKeypointTask } from '../../../../core/projects/utils';
import { useStreamingVideoPlayer } from '../../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ExplanationToolbar } from './explanation-toolbar.component';

export const KEYPOINT_DISABLE_MESSAGE = 'Explanation maps are not available for keypoint detection tasks.';

export const ExplanationSecondaryToolbar = (): JSX.Element => {
    const { tasks, selectedTask } = useTask();
    const { isPlaying } = useStreamingVideoPlayer();
    const { explanations } = usePrediction();
    const isAllTask = tasks.length > 1 && isNil(selectedTask);
    const isKeypointDetection = tasks.some(isKeypointTask);

    return (
        <ExplanationToolbar
            explanations={explanations ?? []}
            isDisabled={isAllTask || isPlaying || isKeypointDetection}
            disabledTooltip={isKeypointDetection ? KEYPOINT_DISABLE_MESSAGE : undefined}
        />
    );
};
