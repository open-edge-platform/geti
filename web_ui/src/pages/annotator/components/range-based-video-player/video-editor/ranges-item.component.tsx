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

import { Flex, View } from '@adobe/react-spectrum';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { TruncatedTextWithTooltip } from '../../../../../shared/components/truncated-text/truncated-text.component';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { ClassificationRanges } from './classification-ranges.component';
import { CreateRange } from './create-range.component';

interface LabelsProps {
    labelGroupName: string;
}

const Labels = ({ labelGroupName }: LabelsProps) => {
    return (
        <View backgroundColor='gray-100' gridColumn={'1 / 2'}>
            <Flex direction='column' gap='size-100' justifyContent='end' height='100%'>
                <View backgroundColor='gray-200' paddingX='size-50' height='size-225'>
                    <TruncatedTextWithTooltip>{labelGroupName}</TruncatedTextWithTooltip>
                </View>
            </Flex>
        </View>
    );
};

interface RangesItemProps {
    maxFrame: number;
    ranges: LabeledVideoRange[];
    newRange: [number, number] | null;
    setNewRange: (range: [number, number] | null) => void;
    sliderValue: number;
    isRangeSelectionEnabled: boolean;
    labelsGroup: Label[];
    onSelectLabelForRange: (label: Label, range?: LabeledVideoRange) => void;
    showResizeIcons: boolean;
    labelGroupName: string;
}

export const RangesItem: FC<RangesItemProps> = ({
    sliderValue,
    isRangeSelectionEnabled,
    maxFrame,
    newRange,
    onSelectLabelForRange,
    setNewRange,
    showResizeIcons,
    labelsGroup,
    labelGroupName,
    ranges,
}) => {
    return (
        <>
            <Labels labelGroupName={labelGroupName} />

            <View
                position='relative'
                gridColumn={'2 / 3'}
                data-testid={`ranges-item-${idMatchingFormat(labelGroupName)}-id`}
                id={`ranges-item-${idMatchingFormat(labelGroupName)}-id`}
            >
                <View backgroundColor='gray-200' height='size-225'>
                    <ClassificationRanges
                        // We want to force the ranges slider to rerender so that the useSliderState hook resets
                        // whenever we change the amount of ranges.
                        key={ranges.length}
                        ranges={ranges}
                        frames={maxFrame}
                        isDisabled={newRange !== null}
                        labels={labelsGroup}
                        onSelectLabelForRange={onSelectLabelForRange}
                    />
                    {isRangeSelectionEnabled && (
                        <CreateRange
                            minValue={0}
                            maxValue={maxFrame}
                            range={newRange}
                            setRange={setNewRange}
                            videoTimelineValue={sliderValue}
                            labels={labelsGroup}
                            onSelectLabelForRange={onSelectLabelForRange}
                            showResizeIcons={showResizeIcons}
                        />
                    )}
                </View>
            </View>
        </>
    );
};
