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

import { Text } from '@adobe/react-spectrum';

import { Performance } from '../../../../core/projects/task.interface';
import { formatPerformanceScore } from '../utils';

interface TooltipContentProps {
    performance: Performance;
    isTaskChainProject: boolean;
}

export const ProjectPerformanceTooltip = ({ performance, isTaskChainProject }: TooltipContentProps) => {
    if (performance.type === 'anomaly_performance') {
        return (
            <>
                <Text>Classification score: {formatPerformanceScore(performance.globalScore)}</Text>
                <br />
                <Text>Localization score: {formatPerformanceScore(performance.localScore)}</Text>
            </>
        );
    }

    if (isTaskChainProject) {
        return (
            <Text>
                The project score for a task-chain project is the average of the performance of the latest model for
                each task. Click here to go to the models page.
            </Text>
        );
    }

    return <Text>Latest project score</Text>;
};
