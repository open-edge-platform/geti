// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';

import { AccuracyHalfDonutChart } from '../project-models/models-container/model-card/accuracy-container/accuracy-half-donut-chart';

import classes from './tests.module.scss';

interface AccuracyTestCellProps {
    id: string;
    score: number;
    testName: string;
    scoreDescription: string;
    shouldShowGlobalLocalScore: boolean;
}

export const AccuracyTestCell = ({
    id,
    score,
    testName,
    scoreDescription,
    shouldShowGlobalLocalScore,
}: AccuracyTestCellProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} direction={'column'} id={`row-${id}-scoreValue-id`} height={'size-400'}>
            <AccuracyHalfDonutChart
                ariaLabel={`${testName} score`}
                id={`row-${id}-accuracy-id`}
                value={Number(score)}
                size={'S'}
            />

            {shouldShowGlobalLocalScore && (
                <Text UNSAFE_className={classes.subtextCell} id={`row-${id}-score-description-scoreValue-id`}>
                    {scoreDescription}
                </Text>
            )}
        </Flex>
    );
};
