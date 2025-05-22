// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useNumberFormatter } from '@geti/ui';
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
