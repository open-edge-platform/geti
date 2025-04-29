// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
