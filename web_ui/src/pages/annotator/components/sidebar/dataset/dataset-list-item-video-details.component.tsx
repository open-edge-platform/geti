// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';

import { useDurationText } from '../../../../../shared/hooks/data-format/use-duration-text.hook';
import { useFramesText } from '../../../../../shared/hooks/data-format/use-frames-text.hook';

interface DatasetListItemVideoDetailsProps {
    className: string;
    frames: number | undefined;
    duration: number;
}
export const DatasetListItemVideoDetails = ({
    className,
    frames,
    duration,
}: DatasetListItemVideoDetailsProps): JSX.Element => {
    const framesText = useFramesText(frames);
    const durationText = useDurationText(duration);

    return (
        <View width={'inherit'} UNSAFE_className={className}>
            <>{isEmpty(framesText) ? durationText : `${framesText} --- ${durationText}`}</>
        </View>
    );
};
