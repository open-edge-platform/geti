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

import { useNumberFormatter } from '@adobe/react-spectrum';
import { useSliderState } from 'react-stately';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { RangeSection } from './range-section.component';

interface ClassificationRangesProps {
    isDisabled?: boolean;
    ranges: LabeledVideoRange[];
    frames: number;
    labels: Label[];
    onSelectLabelForRange: (label: Label, range?: LabeledVideoRange) => void;
}

export const ClassificationRanges = ({
    ranges,
    frames,
    isDisabled = false,
    labels,
    onSelectLabelForRange,
}: ClassificationRangesProps) => {
    const value = ranges.map(({ end }) => end).slice(0, -1);

    const props = {
        value,
        isDisabled,
        minValue: 0,
        maxValue: frames,
        step: 1,
        label: undefined,
        'aria-label': 'Resize ranges',
    };

    const numberFormatter = useNumberFormatter({});

    const state = useSliderState({
        ...props,
        numberFormatter,
    });

    return (
        <>
            {ranges.map((range, idx) => {
                const leftPercentage = idx === 0 ? 0 : state.getThumbPercent(idx - 1);
                const rightPercentage = idx === ranges.length - 1 ? 1.0 : state.getThumbPercent(idx);

                return (
                    <RangeSection
                        key={`${range.start}-${range.end}-${range.labels.map((label) => label.id).join('-')}`}
                        range={range}
                        leftPercentage={leftPercentage}
                        rightPercentage={rightPercentage}
                        labels={labels}
                        onSelectLabelForRange={onSelectLabelForRange}
                        isDisabled={isDisabled}
                    />
                );
            })}
        </>
    );
};
