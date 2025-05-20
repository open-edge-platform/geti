// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@geti/ui';
import {
    CartesianGrid,
    Label,
    ReferenceArea,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';

import { ObjectSizeDistribution } from '../../../../../../core/statistics/services/dataset-statistics.interface';
import { CustomTooltipWrapper } from '../../../../../../shared/components/charts/custom-tooltip-wrapper/custom-tooltip-wrapper.component';
import { SvgLegend } from '../../../../../../shared/components/download-graph-menu/export-svg-utils';
import { withDownloadableSvg } from '../../../../../../shared/components/download-graph-menu/with-downloadable-svg.hoc';
import { DistributionEllipse } from './distribution-ellipse.component';
import { DistributionTriangle } from './distribution-triangle.component';
import { calculateHorizontalTrianglePoints, calculateVerticalTrianglePoints, getScatterPoints } from './utils';

import classes from './distribution-chart.module.scss';

interface DistributionChartProps {
    title: string;
    legend: SvgLegend[];
    objectSizeDistribution: ObjectSizeDistribution;
}
const DownloadableScatterChart = withDownloadableSvg(ScatterChart);

export const DistributionChart = ({ title, objectSizeDistribution, legend }: DistributionChartProps): JSX.Element => {
    const { sizeDistribution, clusterWidthHeight, clusterCenter, aspectRatioThresholdWide, aspectRatioThresholdTall } =
        objectSizeDistribution;
    const [rx, ry] = clusterWidthHeight;
    const [cx, cy] = clusterCenter;

    const { pointsWithinVerticalTriangle, pointsWithinHorizontalTriangle, restPoints } = getScatterPoints(
        sizeDistribution,
        aspectRatioThresholdTall ?? 0,
        aspectRatioThresholdWide ?? 0
    );
    const maxXValue = Math.max(...sizeDistribution.map(([xValue]) => xValue));
    const maxYValue = Math.max(...sizeDistribution.map(([_, yValue]) => yValue));

    const hasAnnotations = aspectRatioThresholdWide !== null && aspectRatioThresholdTall !== null;

    // This offset has a higher value than the actual maximum X or Y. It is also a multiple of 100 to avoid
    // weird limits.
    // Example: if the maxXValue is 133, the roundedMaxX would be Math.ceil(133 / 100) * 100 + 50 = 250
    // So, it's an even, bigger value than the actual max.
    const offset = 100;
    const roundedMaxX = Math.ceil(maxXValue / offset) * offset + offset / 2;
    const roundedMaxY = Math.ceil(maxYValue / offset) * offset + offset / 2;

    return (
        <View height={'size-6000'} marginBottom={'size-400'} UNSAFE_className={classes.distributionChart}>
            <ResponsiveContainer width={'98%'} height={'98%'}>
                <DownloadableScatterChart
                    title={title}
                    legend={legend}
                    margin={{
                        top: 40,
                        bottom: 20,
                        left: 50,
                        right: 75,
                    }}
                >
                    <CartesianGrid stroke={'#484A50'} />
                    <XAxis
                        dataKey='x'
                        name='width'
                        type='number'
                        domain={[0, hasAnnotations ? roundedMaxX : 100]}
                        stroke={'var(--spectrum-global-color-gray-800)'}
                        fontSize={'var(--spectrum-global-dimension-font-size-300)'}
                        dy={15}
                    >
                        <Label
                            value={'Width'}
                            position={'insideBottomRight'}
                            dy={-18}
                            dx={62}
                            fill={'var(--spectrum-global-color-gray-800)'}
                            style={{ letterSpacing: 'size-50' }}
                            fontSize={'var(--spectrum-global-dimension-font-size-200)'}
                            fontWeight={'var(--spectrum-global-font-weight-medium)'}
                        />
                    </XAxis>
                    <YAxis
                        dataKey='y'
                        type='number'
                        name='height'
                        domain={[0, hasAnnotations ? roundedMaxY : 100]}
                        stroke={'var(--spectrum-global-color-gray-800)'}
                        fontSize={'var(--spectrum-global-dimension-font-size-300)'}
                        dx={-13}
                    >
                        <Label
                            value={'Height'}
                            position={'insideTopLeft'}
                            dy={-40}
                            dx={32}
                            fill={'var(--spectrum-global-color-gray-800)'}
                            style={{ letterSpacing: 'size-50' }}
                            fontSize={'var(--spectrum-global-dimension-font-size-200)'}
                            fontWeight={'var(--spectrum-global-font-weight-medium)'}
                        />
                    </YAxis>
                    <Tooltip<number, 'width' | 'height'>
                        cursor={{ strokeDasharray: '3 3' }}
                        animationDuration={0}
                        content={(tooltip) => {
                            const payload = tooltip.payload;
                            if (payload === undefined) {
                                return <></>;
                            }

                            const width = payload.find(({ name }) => name === 'width');
                            const height = payload.find(({ name }) => name === 'height');

                            if (width?.value === undefined || height?.value === undefined) {
                                return <></>;
                            }

                            return (
                                <CustomTooltipWrapper>
                                    <Flex direction={'column'}>
                                        <Text>Width: {Math.round(width.value)}</Text>
                                        <Text>Height: {Math.round(height.value)}</Text>
                                    </Flex>
                                </CustomTooltipWrapper>
                            );
                        }}
                    />
                    <Scatter data={pointsWithinVerticalTriangle} fill='var(--wide-distribution)' />
                    <Scatter data={pointsWithinHorizontalTriangle} fill='var(--tall-distribution)' />
                    <Scatter data={restPoints} fill='#82ca9d' />
                    {aspectRatioThresholdWide !== null && aspectRatioThresholdTall !== null && (
                        <>
                            <ReferenceArea
                                shape={(props) => (
                                    <DistributionEllipse
                                        {...props}
                                        cx={cx}
                                        cy={cy}
                                        rx={rx}
                                        ry={ry}
                                        maxXValue={roundedMaxX}
                                        maxYValue={roundedMaxY}
                                    />
                                )}
                            />
                            <ReferenceArea
                                shape={(props) => (
                                    <DistributionTriangle
                                        {...props}
                                        points={calculateVerticalTrianglePoints(
                                            props,
                                            roundedMaxX,
                                            roundedMaxY,
                                            aspectRatioThresholdTall
                                        )}
                                        fill={'#86B3CA'}
                                    />
                                )}
                            />
                            <ReferenceArea
                                shape={(props) => (
                                    <DistributionTriangle
                                        {...props}
                                        points={calculateHorizontalTrianglePoints(
                                            props,
                                            roundedMaxX,
                                            roundedMaxY,
                                            aspectRatioThresholdWide
                                        )}
                                        fill={'#CC94DA'}
                                    />
                                )}
                            />
                        </>
                    )}
                </DownloadableScatterChart>
            </ResponsiveContainer>
        </View>
    );
};
