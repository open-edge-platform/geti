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

import { Flex, View } from '@adobe/react-spectrum';

import { ModelPerformance as ModelPerformanceInterface } from '../../../../../../core/models/models.interface';
import { PerformanceType } from '../../../../../../core/projects/task.interface';
import { AccuracyContainer } from './accuracy-container/accuracy-container.component';
import {
    ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE,
    ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE,
    ANOMALY_OBJECT_PERFORMANCE_TOOLTIP_MESSAGE,
    DEFAULT_PERFORMANCE_TOOLTIP_MESSAGE,
} from './utils';

interface ModelPerformanceProps {
    performance: ModelPerformanceInterface;
    genericId: string;
    isDisabled?: boolean;
}

export const ModelPerformance = ({ performance, genericId, isDisabled }: ModelPerformanceProps) => {
    if (performance.type === PerformanceType.DEFAULT) {
        return (
            <AccuracyContainer
                isDisabled={isDisabled}
                tooltip={DEFAULT_PERFORMANCE_TOOLTIP_MESSAGE}
                value={performance.score}
                id={genericId}
                heading='Score'
            />
        );
    }

    return (
        <Flex direction='row' gap='size-100'>
            <View>
                <AccuracyContainer
                    isDisabled={isDisabled}
                    tooltip={ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE}
                    value={performance.globalScore}
                    id={`${genericId}-image-score`}
                    heading='Image score'
                />
            </View>
            <View>
                <AccuracyContainer
                    isDisabled={isDisabled}
                    tooltip={
                        performance.localScore === null
                            ? ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE
                            : ANOMALY_OBJECT_PERFORMANCE_TOOLTIP_MESSAGE
                    }
                    value={performance.localScore}
                    id={`${genericId}-object-score`}
                    heading='Object score'
                />
            </View>
        </Flex>
    );
};
