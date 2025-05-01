// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useDurationText } from '@shared/hooks/data-format/use-duration-text.hook';

import { VideoItemDataIndicator } from './video-item-data-indicator.component';

interface VideoDurationDetailsVideIndicatorProps {
    duration: number;
    tooltip: string;
}
export const VideoDurationDetailsViewIndicator = ({
    duration,
    tooltip,
}: VideoDurationDetailsVideIndicatorProps): JSX.Element => {
    const durationText = useDurationText(duration);

    return (
        <VideoItemDataIndicator tooltip={tooltip} id={'video-indicator-duration-id'}>
            {durationText}
        </VideoItemDataIndicator>
    );
};
