// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, useNumberFormatter, View } from '@adobe/react-spectrum';
import { dimensionValue, useMediaQuery } from '@react-spectrum/utils';

import { trimText } from '../../../../../shared/utils';
import { isLargeSizeQuery, isMediumLargeSizeQuery } from '../../../../../theme/queries';
import { ProgressBar } from './progress-bar.component';

import classes from './training-progress.module.scss';

export interface TrainingDetails {
    message: string;
    progress: number | undefined;
}

interface TrainingProgressProps {
    training: TrainingDetails;
}

export const TrainingProgress = ({ training }: TrainingProgressProps): JSX.Element => {
    const formatter = useNumberFormatter({ style: 'percent', maximumFractionDigits: 0 });

    const { message, progress } = training;

    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const isMediumLargeSize = useMediaQuery(isMediumLargeSizeQuery);
    const progressWidth = dimensionValue(isMediumLargeSize || !isLargeSize ? 'size-1700' : 'size-3400');

    return (
        <View height='100%' id='training-progress'>
            <Flex
                height='size-400'
                position='absolute'
                alignItems='center'
                aria-label='training progress'
                justifyContent='space-around'
                UNSAFE_className={classes.container}
            >
                <Text
                    marginEnd={6}
                    id='training-progress-message'
                    aria-label='training progress message'
                    UNSAFE_className={classes.text}
                >
                    {trimText(message, isMediumLargeSize || !isLargeSize ? 18 : 42)}
                </Text>
                {progress !== undefined && progress > 0 && (
                    <Text
                        id='training-progress-percentage'
                        data-testid='training-progress-percentage'
                        UNSAFE_className={classes.text}
                        aria-label='training progress percentage'
                    >
                        {formatter.format(progress / 100)}
                    </Text>
                )}
            </Flex>

            <ProgressBar
                completed={progress ?? 0}
                width={progressWidth}
                progressBarColor='var(--energy-blue-shade-darker)'
                backgroundColor='var(--spectrum-global-color-gray-200)'
            />
        </View>
    );
};
