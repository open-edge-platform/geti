// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text } from '@adobe/react-spectrum';

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
