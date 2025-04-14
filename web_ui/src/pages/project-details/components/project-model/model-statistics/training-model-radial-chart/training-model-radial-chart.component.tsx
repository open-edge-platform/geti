// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
