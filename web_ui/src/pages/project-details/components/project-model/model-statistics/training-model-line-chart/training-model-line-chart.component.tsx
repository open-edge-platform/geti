// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CardContent } from '@shared/components/card-content/card-content.component';
import { LineChart } from '@shared/components/charts/line-chart/line-chart.component';
import { LineChartData } from '@shared/components/charts/line-chart/line-chart.interface';
import { FullscreenAction } from '@shared/components/fullscreen-action/fullscreen-action.component';

import {
    TrainingModelChartConfig,
    TrainingModelLineChartType,
} from '../../../../../../core/statistics/model-statistics.interface';
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
