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
    TrainingModelBarRadialChart,
    TrainingModelChartConfig,
} from '../../../../../../core/statistics/model-statistics.interface';
import { CardContent } from '../../../../../../shared/components/card-content/card-content.component';
import { BarHorizontalChart } from '../../../../../../shared/components/charts/bar-horizontal-chart/bar-horizontal-chart.component';
import { Colors } from '../../../../../../shared/components/charts/chart.interface';
import { convertColorToFadedColor } from '../../../../../../shared/components/charts/utils';
import { FullscreenAction } from '../../../../../../shared/components/fullscreen-action/fullscreen-action.component';
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
