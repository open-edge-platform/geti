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
import { RadialChart } from '../../../../../../shared/components/charts/radial-chart/radial-chart.component';
import { getDistinctColorBasedOnHash } from '../../../../../create-project/components/distinct-colors';

export const TrainingModelRadialChart = ({
    header,
    value,
    inCard = true,
}: TrainingModelBarRadialChart & TrainingModelChartConfig): JSX.Element => {
    const hasOnlyOneRing = value.length === 1;
    const radialData = value.map(({ header: labelHeader, value: labelValue, color }) => ({
        name: labelHeader,
        fill: color ?? (hasOnlyOneRing ? 'var(--default-chart-color)' : getDistinctColorBasedOnHash(labelHeader)),
        value: labelValue * 100,
    }));

    return inCard ? (
        <CardContent
            isDownloadable
            title={header}
            flexBasis={'33%'}
            downloadableData={{ type: 'barChart', data: radialData }}
            height={'100%'}
        >
            <RadialChart title={header} data={radialData} legend />
        </CardContent>
    ) : (
        <RadialChart title={header} data={radialData} legend />
    );
};
