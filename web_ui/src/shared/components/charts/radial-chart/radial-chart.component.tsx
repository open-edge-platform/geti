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
