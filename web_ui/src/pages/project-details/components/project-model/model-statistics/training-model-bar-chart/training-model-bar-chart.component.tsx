// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CardContent } from '@shared/components/card-content/card-content.component';
import { BarHorizontalChart } from '@shared/components/charts/bar-horizontal-chart/bar-horizontal-chart.component';
import { Colors } from '@shared/components/charts/chart.interface';
import { convertColorToFadedColor } from '@shared/components/charts/utils';
import { FullscreenAction } from '@shared/components/fullscreen-action/fullscreen-action.component';

import {
    TrainingModelBarRadialChart,
    TrainingModelChartConfig,
} from '../../../../../../core/statistics/model-statistics.interface';
import { getDistinctColorBasedOnHash } from '../../../../../create-project/components/distinct-colors';

const TrainingModelBarChart = ({
    header,
    value,
    inCard = true,
}: TrainingModelBarRadialChart & TrainingModelChartConfig): JSX.Element => {
    const colors: Colors[] = [];

    const hasOnlyOneBar = value.length === 1;
    const barData = value.map(({ value: labelValue, header: labelHeader, color }) => {
        // #8DAE46 is a default chart color, stored in the hex format due to conversion function below,
        const barColor = color ?? (hasOnlyOneBar ? '#8BAE46' : getDistinctColorBasedOnHash(labelHeader));
        colors.push({ color: barColor, fadedColor: convertColorToFadedColor(barColor, 50) });

        return {
            name: labelHeader,
            value: labelValue,
        };
    });

    if (inCard) {
        return (
            <CardContent
                isDownloadable
                downloadableData={{ type: 'barChart', data: barData }}
                title={header}
                actions={
                    <FullscreenAction
                        isDownloadable
                        title={header}
                        downloadableData={{ type: 'barChart', data: barData }}
                    >
                        <BarHorizontalChart title={header} data={barData} barSize={40} colors={colors} />
                    </FullscreenAction>
                }
                height={'100%'}
            >
                <BarHorizontalChart title={header} data={barData} barSize={20} colors={colors} />
            </CardContent>
        );
    }

    return <BarHorizontalChart title={header} data={barData} barSize={20} colors={colors} />;
};

export default TrainingModelBarChart;
