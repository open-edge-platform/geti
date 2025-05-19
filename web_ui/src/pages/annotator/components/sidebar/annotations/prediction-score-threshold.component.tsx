// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DialogTrigger, Flex, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { ActionButton, Slider } from '@geti/ui';

import { ChevronDownLight } from '../../../../../assets/icons';
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
