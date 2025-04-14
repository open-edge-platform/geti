// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Legend, PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';

import { withDownloadableSvg } from '../../download-graph-menu/with-downloadable-svg.hoc';
import { ChartData } from '../chart.interface';

interface RadialData extends ChartData {
    fill?: string;
}

interface RadialChartProps {
    title: string;
    circleSize?: number;
    innerRadius?: number;
    children?: ReactNode;
    data: RadialData[];
    legend?: boolean;
}

const DownloadableRadialBarChart = withDownloadableSvg(RadialBarChart);

export const RadialChart = ({
    data,
    title,
    children,
    circleSize = 100,
    innerRadius = 80,
    legend,
}: RadialChartProps): JSX.Element => {
    return (
        <ResponsiveContainer width={'98%'} height={'98%'}>
            <DownloadableRadialBarChart
                data={data}
                title={title}
                endAngle={-270}
                startAngle={90}
                width={circleSize}
                height={circleSize}
                legend={data.map((item: RadialData) => ({
                    color: item.fill ?? '',
                    name: `${item.name} ${item.value / 100}`,
                }))}
                innerRadius={innerRadius}
            >
                <PolarAngleAxis type='number' domain={[0, 100]} angleAxisId={0} tick={false} />
                <RadialBar
                    dataKey='value'
                    name={'label'}
                    background={{ fill: 'var(--spectrum-global-color-gray-300)' }}
                    aria-label={data[0].name}
                    aria-valuenow={data[0].value}
                />
                {legend && (
                    <Legend
                        align={'left'}
                        iconType={'square'}
                        payload={data.map((item: RadialData) => ({
                            id: item.name,
                            type: 'square',
                            value: `${item.name} ${item.value / 100}`,
                            color: item.fill,
                        }))}
                    />
                )}
                {children}
            </DownloadableRadialBarChart>
        </ResponsiveContainer>
    );
};
