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
    TrainingModelChartConfig,
    TrainingModelLineChartType,
} from '../../../../../../core/statistics/model-statistics.interface';
import { CardContent } from '../../../../../../shared/components/card-content/card-content.component';
import { LineChart } from '../../../../../../shared/components/charts/line-chart/line-chart.component';
import { LineChartData } from '../../../../../../shared/components/charts/line-chart/line-chart.interface';
import { FullscreenAction } from '../../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { getDistinctColorBasedOnHash } from '../../../../../create-project/components/distinct-colors';

export const TrainingModelLineChart = ({
    header,
    value,
    inCard = true,
}: TrainingModelLineChartType & TrainingModelChartConfig): JSX.Element => {
    const { lineData, xAxisLabel, yAxisLabel } = value;

    const hasOnlyOneLine = lineData.length === 1;
    const convertedLineData: LineChartData[] = lineData.map(({ points, header: labelHeader, color }) => ({
        name: labelHeader,
        color: color ?? (hasOnlyOneLine ? 'var(--default-chart-color)' : getDistinctColorBasedOnHash(labelHeader)),
        points,
    }));

    const chartComponent = (
        <LineChart title={header} data={convertedLineData} xAxisLabel={xAxisLabel} yAxisLabel={yAxisLabel} />
    );

    if (!inCard) {
        return chartComponent;
    }

    return (
        <CardContent
            title={header}
            isDownloadable
            downloadableData={{ type: 'lineChart', data: convertedLineData, xLabel: xAxisLabel, yLabel: yAxisLabel }}
            actions={
                <FullscreenAction
                    isDownloadable
                    title={header}
                    downloadableData={{
                        type: 'lineChart',
                        data: convertedLineData,
                        xLabel: xAxisLabel,
                        yLabel: yAxisLabel,
                    }}
                >
                    {chartComponent}
                </FullscreenAction>
            }
            height={'100%'}
        >
            {chartComponent}
        </CardContent>
    );
};
