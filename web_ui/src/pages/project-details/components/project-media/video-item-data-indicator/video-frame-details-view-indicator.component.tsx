// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useFramesText } from '../../../../../shared/hooks/data-format/use-frames-text.hook';
import { VideoItemDataIndicator } from './video-item-data-indicator.component';

interface VideoFrameDetailsVideIndicatorProps {
    frames: number;
    tooltip: string;
}
export const VideoFrameDetailsViewIndicator = ({
    frames,
    tooltip,
}: VideoFrameDetailsVideIndicatorProps): JSX.Element => {
    const frameText = useFramesText(frames);

    return (
        <VideoItemDataIndicator tooltip={tooltip} id={'video-indicator-frames-id'}>
            {frameText}
        </VideoItemDataIndicator>
    );
};
