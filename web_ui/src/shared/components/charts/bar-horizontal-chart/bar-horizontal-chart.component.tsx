// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, MutableRefObject, useEffect, useMemo, useRef, useState } from 'react';

import { Flex, Text } from '@geti/ui';
import { isFunction } from 'lodash-es';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { trimText } from '../../../utils';
import { withDownloadableSvg } from '../../download-graph-menu/with-downloadable-svg.hoc';
import { ChartProps, Colors } from '../chart.interface';
import { CHARACTER_WIDTH } from '../utils';
import { CustomTooltipChart } from './custom-tooltip/custom-tooltip.component';

import classes from './bar-horizontal-chart.module.scss';

type FormatTooltipMessage = ComponentProps<typeof CustomTooltipChart>['displayMessage'];

type XTickFormatter = ComponentProps<typeof XAxis>['tickFormatter'];

export interface BarHorizontalChartProps extends ChartProps {
    barSize?: number;
    xPadding?: {
        right?: number;
        left?: number;
    };
    yPadding?: {
        top?: number;
        bottom?: number;
    };
    colors?: Colors[];
    allowDecimals?: boolean;
    formatTooltipMessage?: FormatTooltipMessage;
    xTickFormatter?: XTickFormatter;
    ariaLabel?: string;
    onCellClick?: (labelName: string) => void;
}

const LEFT_MARGIN = -70;
const MAX_LABEL_LENGTH = 18;
// Value set after tests to not have too 'crowded' chart
const BAR_MARGIN_SIZE = 5;
const MIN_BAR_SIZE_WITH_MARGIN = 25 + BAR_MARGIN_SIZE;

const DownloadableBarChart = withDownloadableSvg(BarChart);

const displayMessage: FormatTooltipMessage = ({ value, label }) => (
    <Flex direction={'column'}>
        <Text>Label: {label}</Text>
        <Text>Value: {value}</Text>
    </Flex>
);

export const BarHorizontalChart = ({
    title,
    data,
    barSize = 20,
    yPadding,
    xPadding,
    colors,
    xTickFormatter,
    ariaLabel,
    allowDecimals = true,
    formatTooltipMessage = displayMessage,
    onCellClick,
}: BarHorizontalChartProps): JSX.Element => {
    const [labelColors, setLabelColors] = useState<Colors[]>(colors || []);
    const [margin, setMargin] = useState<number>(0);
    const container = useRef<HTMLDivElement | null>(null);
    const prevHoveredLabel = useRef<string | null>(null);

    const yAxisFormatter = (label: string | number | undefined): string => {
        if (typeof label === 'string') {
            const formattedLabel = trimText(label, MAX_LABEL_LENGTH);
            const calcMargin = formattedLabel.length * CHARACTER_WIDTH;

            setMargin((prevMargin) => (prevMargin < calcMargin ? calcMargin : prevMargin));

            return formattedLabel;
        }

        return `${label}`;
    };

    useEffect(() => {
        colors && setLabelColors(colors);
    }, [colors]);

    useEffect(() => {
        if (container.current) {
            container.current.scrollTop = container.current.scrollHeight;
        }
    }, []);

    const minHeight = useMemo(() => {
        // Remove margin from last bar
        return data.length * MIN_BAR_SIZE_WITH_MARGIN - BAR_MARGIN_SIZE;
    }, [data.length]);

    return (
        <div style={{ overflow: 'auto', height: '100%', width: '100%' }} ref={container} aria-label={ariaLabel}>
            <ResponsiveContainer minHeight={minHeight} height={'98%'} width={'98%'}>
                <DownloadableBarChart
                    data={data}
                    title={title}
                    layout='vertical'
                    barSize={barSize}
                    className={classes.barChart}
                    margin={{ left: LEFT_MARGIN + margin, right: 20 }}
                >
                    <CartesianGrid horizontal={false} className={classes.barChartCartesianStroke} />
                    <XAxis
                        type='number'
                        dataKey='value'
                        axisLine={false}
                        tickLine={false}
                        padding={xPadding}
                        allowDecimals={allowDecimals}
                        id='bar-horizontal-chart-xaxis-id'
                        tickFormatter={xTickFormatter}
                    />
                    <YAxis
                        type='category'
                        dataKey='name'
                        axisLine={false}
                        tickLine={false}
                        padding={yPadding}
                        width={100}
                        tickFormatter={yAxisFormatter}
                        id='bar-horizontal-chart-yaxis-id'
                        minTickGap={0}
                    />
                    <Tooltip
                        animationDuration={0}
                        content={
                            <CustomTooltipChart
                                prevHoveredLabel={prevHoveredLabel as MutableRefObject<string>}
                                defaultColors={colors || []}
                                setLabelColors={setLabelColors}
                                data={data}
                                displayMessage={formatTooltipMessage}
                            />
                        }
                    />

                    <Bar dataKey='value' radius={[0, 2, 2, 0]}>
                        {data.length ? (
                            data.map(({ name, value }, index) => (
                                <Cell
                                    key={name}
                                    fill={
                                        labelColors.length && labelColors[index] ? labelColors[index].color : '#8BAE46'
                                    }
                                    id={`${name}-id`}
                                    aria-label={name}
                                    aria-valuenow={value}
                                    onClick={isFunction(onCellClick) ? () => onCellClick(name) : undefined}
                                />
                            ))
                        ) : (
                            <></>
                        )}
                    </Bar>
                </DownloadableBarChart>
            </ResponsiveContainer>
        </div>
    );
};
