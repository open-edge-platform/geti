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

import { useNumberFormatter } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';
import { Cell, Label, Pie, PieChart as RePieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { SvgLegend } from '../../download-graph-menu/export-svg-utils';
import { withDownloadableSvg } from '../../download-graph-menu/with-downloadable-svg.hoc';
import { PieCustomTooltip } from './pie-custom-tooltip.component';

interface PieChartProps {
    title: string;
    legend: SvgLegend[];
    data: {
        name: string | null;
        value: number;
        color: string;
    }[];
    ariaLabel?: string;
}

const DownloadablePieChart = withDownloadableSvg(RePieChart);

export const PieChart = ({ title, data, legend, ariaLabel }: PieChartProps): JSX.Element => {
    const totalSum = data.reduce<number>((prev, curr) => prev + curr.value, 0);
    const formatter = useNumberFormatter({ notation: 'compact', compactDisplay: 'short' });
    const isNoObject = !isEmpty(data) && data[0].name === null;

    return (
        <ResponsiveContainer width={140} height={140}>
            <DownloadablePieChart title={title} legend={legend} margin={{ top: -6, left: -11, bottom: -6, right: -11 }}>
                <Pie
                    data={data}
                    dataKey='value'
                    innerRadius={'75%'}
                    outerRadius={'90%'}
                    paddingAngle={isNoObject ? 0 : 2}
                >
                    <Label
                        position='center'
                        dy={-8}
                        fontSize={dimensionValue('size-400')}
                        fill={'var(--spectrum-global-color-gray-800)'}
                        aria-label={ariaLabel}
                    >
                        {formatter.format(isNoObject ? 0 : totalSum)}
                    </Label>
                    <Label
                        position='center'
                        dy={18}
                        fill={'var(--spectrum-global-color-gray-700)'}
                        fontSize={dimensionValue('size-175')}
                    >
                        Objects
                    </Label>

                    {data.map(({ name, color }) => (
                        <Cell key={`cell-${name}`} fill={color} stroke={color} />
                    ))}
                </Pie>

                {!isNoObject && <Tooltip content={<PieCustomTooltip total={totalSum} />} />}
            </DownloadablePieChart>
        </ResponsiveContainer>
    );
};
