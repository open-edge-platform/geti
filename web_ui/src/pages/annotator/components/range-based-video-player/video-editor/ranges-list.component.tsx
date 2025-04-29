// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
