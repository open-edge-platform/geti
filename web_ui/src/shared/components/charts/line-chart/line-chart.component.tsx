// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useState } from 'react';

import { useNumberFormatter } from 'react-aria';
import { Legend, Line, LineChart as LineChartRecharts, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { withDownloadableSvg } from '../../download-graph-menu/with-downloadable-svg.hoc';
import { ADDITIONAL_MARGIN, CHARACTER_WIDTH, MARGIN_THRESHOLD } from '../utils';
import { CustomTooltipLineChart } from './custom-tooltip/custom-tooltip.component';
import { LineChartProps } from './line-chart.interface';

import classes from './line-chart.module.scss';

const DownloadableLineChart = withDownloadableSvg(LineChartRecharts);

export const LineChart = ({ title, data, xAxisLabel, yAxisLabel }: LineChartProps): JSX.Element => {
    const [margin, setMargin] = useState<number>(0);
    const formatter = useNumberFormatter({
        notation: 'compact',
        maximumFractionDigits: 5,
    });

    const tickFormatter = useCallback(
        // eslint-disable-next-line
        (value: any) => {
            if (typeof value === 'number') {
                return value > 1 ? formatter.format(parseFloat(value.toFixed(2))) : formatter.format(value);
            }
            return value;
        },
        [formatter]
    );

    // eslint-disable-next-line
    const yTickFormatter = (value: any) => {
        let formattedValue = tickFormatter(value);

        if (typeof formattedValue === 'number') {
            formattedValue = formattedValue.toString();
        }

        const calcMargin = formattedValue.length * CHARACTER_WIDTH + ADDITIONAL_MARGIN;
        setMargin((prevMargin) => (prevMargin < calcMargin ? calcMargin : prevMargin));
        return formattedValue;
    };

    return (
        <ResponsiveContainer width={'98%'} height={'98%'}>
            <DownloadableLineChart
                title={title}
                className={classes.lineChartAxis}
                margin={{
                    top: 10,
                    left: margin - MARGIN_THRESHOLD,
                    right: 10,
                    bottom: 5,
                }}
            >
                <XAxis
                    dataKey={'x'}
                    axisLine={true}
                    className={classes.lineChartAxis}
                    allowDuplicatedCategory={false}
                    padding={{ right: 20 }}
                    tickMargin={5}
                    height={55}
                    interval={'preserveStartEnd'}
                    minTickGap={15}
                    tickFormatter={tickFormatter}
                    label={{ value: xAxisLabel, dy: 20 }}
                />
                <YAxis
                    dataKey={'y'}
                    tickLine={false}
                    tickFormatter={yTickFormatter}
                    label={{ value: yAxisLabel, angle: -90, dx: -margin }}
                />
                <Legend iconType={'square'} align={'left'} />
                {data.map(({ points, name, color }) => (
                    <Line
                        dataKey={'y'}
                        data={points}
                        key={name}
                        name={name}
                        stroke={color}
                        activeDot={true}
                        dot={false}
                        aria-label={`${name} line`}
                        aria-valuetext={points.map(({ x, y }) => `x: ${x}, y: ${y}`).join(', ')}
                    />
                ))}
                <Tooltip
                    content={
                        <CustomTooltipLineChart xLabel={xAxisLabel} yLabel={yAxisLabel} formatter={tickFormatter} />
                    }
                />
            </DownloadableLineChart>
        </ResponsiveContainer>
    );
};
