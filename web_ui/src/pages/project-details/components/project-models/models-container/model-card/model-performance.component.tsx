// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
