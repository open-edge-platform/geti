// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, useMediaQuery, useNumberFormatter, View } from '@geti/ui';

import { isLargeSizeQuery, isMediumLargeSizeQuery } from '../../../../../../packages/ui/theme/queries';
import { ProgressBar } from '../../../../../shared/components/progress-bar/progress-bar.component';
import { trimText } from '../../../../../shared/utils';

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

    const { message, progress = 0 } = training;

    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const isMediumLargeSize = useMediaQuery(isMediumLargeSizeQuery);

    return (
        <View height='100%' id='training-progress' position={'relative'}>
            <Flex
                height='size-400'
                alignItems='center'
                aria-label='training progress'
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
                size={'S'}
                value={progress}
                aria-label='job-item-progress-bar'
                UNSAFE_className={classes.progressBar}
            />
        </View>
    );
};
