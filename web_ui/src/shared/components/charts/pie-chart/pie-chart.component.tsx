// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue, useNumberFormatter } from '@geti/ui';
import { isEmpty } from 'lodash-es';
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
