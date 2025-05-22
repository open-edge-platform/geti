// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Flex, Heading, Link, Loading, View, type StyleProps } from '@geti/ui';
import { isEmpty, isString, take } from 'lodash-es';
import { Bar, BarChart, Legend, Rectangle, ResponsiveContainer, Tooltip, TooltipProps, XAxis, YAxis } from 'recharts';

import { useTransactionsQueries } from '../../../core/credits/transactions/hooks/use-transactions.hook';
import { TransactionsAggregatesKey } from '../../../core/credits/transactions/transactions.interface';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { convertColorToFadedColor } from '../../../shared/components/charts/utils';
import { withDownloadableSvg } from '../../../shared/components/download-graph-menu/with-downloadable-svg.hoc';
import { NotFound } from '../../../shared/components/not-found/not-found.component';
import { isNonEmptyArray, pluralize, trimText } from '../../../shared/utils';
import {
    convertAggregatesToProjectsChartData,
    getColorFromServiceName,
    getServiceNamesFromAggregates,
} from './graph-utils';

const BAR_HEIGHT = 32;
const CHARACTER_WIDTH = 8;
const MAX_LABEL_LENGTH = 18;
const AXIS_LABEL_WIDTH = CHARACTER_WIDTH * MAX_LABEL_LENGTH;
const MAX_OPENED_BARS = 5;
const BAR_MARGIN = 32;

const DownloadableBarChart = withDownloadableSvg(BarChart);

const CustomTooltip = <TValue extends number, TName extends string>({
    active,
    payload,
    label,
}: TooltipProps<TValue, TName>) => {
    if (active && isNonEmptyArray(payload)) {
        return (
            <View backgroundColor={'gray-200'} padding={'size-250'}>
                <Heading level={5} margin={0} marginBottom={'size-50'}>
                    Credit consumption by project:
                </Heading>
                <Heading level={6} margin={0} marginBottom={'size-50'}>
                    {label}
                </Heading>
                {payload.map((entry, index) => (
                    <View key={`item-${index}`}>
                        {entry.name}: {pluralize(entry.value || 0, 'credit')}
                    </View>
                ))}
            </View>
        );
    }
    return null;
};

interface ProjectsCreditConsumptionCardProps extends StyleProps {
    fromDate?: Date;
    toDate?: Date;
}

export const ProjectsCreditConsumptionCard = (props: ProjectsCreditConsumptionCardProps): JSX.Element => {
    const { fromDate, toDate, ...styleProps } = props;
    const { useGetTransactionsAggregates } = useTransactionsQueries();
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { data, isPending } = useGetTransactionsAggregates(
        { workspaceId, organizationId },
        {
            keys: new Set([TransactionsAggregatesKey.PROJECT, TransactionsAggregatesKey.SERVICE_NAME]),
            fromDate: fromDate ? fromDate.valueOf().toString() : undefined,
            toDate: toDate ? toDate.valueOf().toString() : undefined,
        }
    );
    const [showAll, setShowAll] = useState(false);
    const serviceNames = useMemo(() => getServiceNamesFromAggregates(data?.aggregates), [data]);
    const chartData = useMemo(
        () => convertAggregatesToProjectsChartData(data?.aggregates, serviceNames),
        [data, serviceNames]
    );

    const yAxisFormatter = (label: string | number | undefined): string =>
        isString(label) ? trimText(label, MAX_LABEL_LENGTH) : `${label}`;

    const chart = showAll ? chartData : take(chartData, MAX_OPENED_BARS);

    return (
        <View backgroundColor={'gray-100'} position={'relative'} minHeight={BAR_HEIGHT + BAR_MARGIN} {...styleProps}>
            {isPending ? (
                <Loading size='S' />
            ) : isEmpty(chart) ? (
                <Flex justifyContent='center' alignItems='center' height='100%'>
                    <View paddingY={'size-500'}>
                        <NotFound />
                    </View>
                </Flex>
            ) : (
                <>
                    <ResponsiveContainer
                        height={'100%'}
                        width={'100%'}
                        minHeight={BAR_HEIGHT * chart.length + BAR_MARGIN}
                    >
                        <DownloadableBarChart
                            title='Credit consumption by projects'
                            layout='vertical'
                            data={chart}
                            barSize={8}
                            barCategoryGap={24}
                            margin={{ left: 16, right: 16, top: 16, bottom: 16 }}
                        >
                            <YAxis
                                type='category'
                                dataKey='label'
                                tickLine={false}
                                axisLine={false}
                                stroke='#FFFFFF'
                                width={AXIS_LABEL_WIDTH}
                                tickFormatter={yAxisFormatter}
                                fontSize={12}
                            />
                            <XAxis type='number' tickLine={false} tick={false} axisLine={false} height={0} />
                            <Tooltip cursor={false} content={CustomTooltip} />
                            <Legend align='right' verticalAlign='top' layout='vertical' iconType='circle' />
                            {serviceNames.map((serviceName, index) => {
                                return (
                                    <Bar
                                        key={serviceName}
                                        name={serviceName}
                                        dataKey={`values.${serviceName}`}
                                        stackId='a'
                                        fill={getColorFromServiceName(serviceName)}
                                        radius={
                                            serviceNames.length > 1
                                                ? index !== 0
                                                    ? index === serviceNames.length - 1
                                                        ? [0, 8, 8, 0]
                                                        : 0
                                                    : [8, 0, 0, 8]
                                                : 8
                                        }
                                        activeBar={
                                            <Rectangle
                                                fill={convertColorToFadedColor(
                                                    getColorFromServiceName(serviceName),
                                                    50
                                                )}
                                            />
                                        }
                                    />
                                );
                            })}
                        </DownloadableBarChart>
                    </ResponsiveContainer>
                    {chartData.length > MAX_OPENED_BARS && !showAll && (
                        <View paddingStart={'size-600'} paddingBottom={'size-300'}>
                            <Link onPress={() => setShowAll(true)}>Show all</Link>
                        </View>
                    )}
                </>
            )}
        </View>
    );
};
