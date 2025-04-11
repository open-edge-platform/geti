// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import {
    ModelMetrics,
    TrainingModelChartConfig,
    TrainingModelInfoType,
    TrainingModelStatistic,
    TrainingModelStatisticsGroup,
} from '../../../../../core/statistics/model-statistics.interface';
import TrainingModelBarChart from './training-model-bar-chart/training-model-bar-chart.component';
import { TrainingModelGrouped } from './training-model-grouped/training-model-grouped.component';
import { TrainingModelLineChart } from './training-model-line-chart/training-model-line-chart.component';
import { TrainingModelMatrix } from './training-model-matrix/training-model-matrix.component';
import { TrainingModelRadialChart } from './training-model-radial-chart/training-model-radial-chart.component';
import { TrainingModelTextChart } from './training-model-text-chart/training-model-text-chart.component';

export const getModelStatisticPresentation = (
    statistic: TrainingModelStatistic | TrainingModelStatisticsGroup,
    options?: TrainingModelChartConfig
): JSX.Element => {
    switch (statistic.type) {
        case 'text':
            return <TrainingModelTextChart value={statistic.value} header={statistic.header} {...options} />;
        case 'line':
            return <TrainingModelLineChart {...statistic} {...options} />;
        case 'bar':
            return <TrainingModelBarChart {...statistic} {...options} />;
        case 'radial_bar':
            return <TrainingModelRadialChart {...statistic} {...options} />;
        case 'matrix':
            return <TrainingModelMatrix gridColumn={'1 / 4'} {...statistic} />;
        case 'group':
            return <TrainingModelGrouped {...statistic} />;
        default:
            return <></>;
    }
};

export enum TrainingMetadataKeys {
    TRAINING_DATE = 'training date',
    TRAINING_JOB = 'training job',
    TRAINING_DURATION = 'training duration',
}

interface GetModelStatistics {
    trainingMetadata: TrainingModelInfoType[];
    trainingMetrics: ModelMetrics;
}

const TRAINING_METADATA: string[] = Object.values(TrainingMetadataKeys);

export const getModelStatistics = (statistics: ModelMetrics) => {
    return statistics.reduce<GetModelStatistics>(
        (acc, curr) => {
            if (
                curr.type === 'text' &&
                TRAINING_METADATA.some((metadata) => curr.header.toLocaleLowerCase().includes(metadata))
            ) {
                if (curr.header.toLocaleLowerCase().includes(TrainingMetadataKeys.TRAINING_DATE)) {
                    return {
                        ...acc,
                        trainingMetadata: [curr as TrainingModelInfoType, ...acc.trainingMetadata],
                    };
                }

                // time value is missing 0 at the beginning, e.g. 4:09:01, we have to add it manually
                const [hr, mm, ss] = curr.value.split(':');
                curr.value = `${hr.length === 1 ? `0${hr}` : hr}:${mm}:${ss}`;

                return {
                    ...acc,
                    trainingMetadata: [...acc.trainingMetadata, curr as TrainingModelInfoType],
                };
            }

            return {
                ...acc,
                trainingMetrics: [...acc.trainingMetrics, curr],
            };
        },
        { trainingMetadata: [], trainingMetrics: [] }
    );
};
