// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Grid } from '@adobe/react-spectrum';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { RangesItem } from './ranges-item.component';
import { getLabelGroupName } from './utils';

interface RangesListProps {
    maxFrame: number;
    ranges: LabeledVideoRange[];
    newRange: [number, number] | null;
    setNewRange: (range: [number, number] | null) => void;
    sliderValue: number;
    isRangeSelectionEnabled: boolean;
    groupedLabels: Record<string, Label[]>;
    onSelectLabelForRange: (label: Label, range?: LabeledVideoRange) => void;
}

export const RangesList: FC<RangesListProps> = ({
    groupedLabels,
    ranges,
    maxFrame,
    newRange,
    setNewRange,
    onSelectLabelForRange,
    isRangeSelectionEnabled,
    sliderValue,
}) => {
    return (
        <Grid columns={['size-2000', '1fr']} marginTop='size-400' rowGap='size-50' gridColumn={'1 / 3'}>
            {Object.entries(groupedLabels).map(([groupName, labelsGroup], index) => {
                const labelGroupName = getLabelGroupName(groupedLabels, index);

                const rangesWithLabelsThatBelongToTheCurrentGroup: LabeledVideoRange[] = ranges.map((range) => ({
                    ...range,
                    labels: range.labels.filter((label) => label.group === groupName),
                }));

                return (
                    <RangesItem
                        key={groupName}
                        labelGroupName={labelGroupName}
                        maxFrame={maxFrame}
                        ranges={rangesWithLabelsThatBelongToTheCurrentGroup}
                        newRange={newRange}
                        setNewRange={setNewRange}
                        sliderValue={sliderValue}
                        isRangeSelectionEnabled={isRangeSelectionEnabled}
                        labelsGroup={labelsGroup}
                        onSelectLabelForRange={onSelectLabelForRange}
                        showResizeIcons={index === 0}
                    />
                );
            })}
        </Grid>
    );
};
