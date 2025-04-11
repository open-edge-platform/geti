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

import { DialogTrigger, Flex, Slider, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { ChevronDownLight } from '../../../../../assets/icons';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { useAnnotationThreshold } from '../../../providers/annotation-threshold-provider/annotation-threshold-provider.component';

import classes from './annotations.module.scss';

interface PredictionScoreThresholdProps {
    isDisabled: boolean;
    tooltip: { enabled: boolean; description: string };
}

export const PredictionScoreThreshold = ({ tooltip, isDisabled }: PredictionScoreThresholdProps): JSX.Element => {
    const { scoreThreshold, setScoreThreshold } = useAnnotationThreshold();

    const hideAndSetScoreThreshold = (newScoreThreshold: number) => {
        setScoreThreshold(newScoreThreshold);
    };

    return (
        <Flex alignContent='center'>
            <TooltipTrigger delay={0} isDisabled={!tooltip.enabled}>
                <ActionButton isQuiet UNSAFE_className={classes.sliderLabel}>
                    Filter by score:
                </ActionButton>
                <Tooltip>{tooltip.description}</Tooltip>
            </TooltipTrigger>
            <DialogTrigger type='popover'>
                <ActionButton
                    alignSelf='center'
                    isDisabled={isDisabled}
                    aria-label='filter-by-score-button'
                    UNSAFE_className={classes.sliderButton}
                >
                    <Text marginEnd='size-50'>{Math.round(scoreThreshold * 100)}</Text>
                    <div style={{ order: 1 }}>
                        <ChevronDownLight width={24} />
                    </div>
                </ActionButton>
                <View paddingTop='size-65' paddingX='size-75' paddingBottom='size-40' width={'size-2400'}>
                    <Slider
                        isFilled
                        width='100%'
                        step={0.01}
                        minValue={0}
                        maxValue={1}
                        value={scoreThreshold}
                        onChange={hideAndSetScoreThreshold}
                        isDisabled={isDisabled}
                        showValueLabel={false}
                        id='filter-by-score-slider'
                        aria-label='filter-by-score-slider'
                    />
                </View>
            </DialogTrigger>
        </Flex>
    );
};
