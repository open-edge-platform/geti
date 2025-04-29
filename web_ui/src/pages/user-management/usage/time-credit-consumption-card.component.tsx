// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useRef, useState } from 'react';

import { ComboBox, Flex, Heading, Item, Key, View } from '@adobe/react-spectrum';
import { dimensionValue, useUnwrapDOMRef } from '@react-spectrum/utils';
import { StyleProps } from '@react-types/shared';
import Close from '@spectrum-icons/workflow/Close';
import dayjs from 'dayjs';
import isEmpty from 'lodash/isEmpty';
import isNumber from 'lodash/isNumber';
import orderBy from 'lodash/orderBy';
import { Bar, BarChart, Rectangle, ResponsiveContainer, Tooltip, TooltipProps, XAxis, YAxis } from 'recharts';

import { useTransactionsQueries } from '../../../core/credits/transactions/hooks/use-transactions.hook';
import { TransactionsAggregatesKey } from '../../../core/credits/transactions/transactions.interface';
import { useProjectActions } from '../../../core/projects/hooks/use-project-actions.hook';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { ActionButton } from '../../../shared/components/button/button.component';
import { convertColorToFadedColor } from '../../../shared/components/charts/utils';
import { withDownloadableSvg } from '../../../shared/components/download-graph-menu/with-downloadable-svg.hoc';
import { Loading } from '../../../shared/components/loading/loading.component';
import { NotFound } from '../../../shared/components/not-found/not-found.component';
import { isNonEmptyArray, pluralize } from '../../../shared/utils';
import { DownloadSvgButton } from '../../project-details/components/project-model/model-statistics/download-svg-button.component';
import {
    convertAggregatesToTimeChartData,
    getColorFromServiceName,
    getServiceNamesFromAggregates,
} from './graph-utils';

import classes from './usage.module.scss';

const MIN_HEIGHT = 368;

const DownloadableBarChart = withDownloadableSvg(BarChart);

interface TimeCreditConsumptionCardProps extends StyleProps {
    fromDate?: Date;
    toDate?: Date;
}

const CustomTooltip = <TValue extends number, TName extends string>({
    active,
    payload,
    label,
}: TooltipProps<TValue, TName>) => {
    if (active && isNonEmptyArray(payload)) {
        return (
            <View backgroundColor={'gray-200'} padding={'size-250'}>
                <Heading level={6} margin={0} marginBottom={'size-50'}>
                    {dayjs(label).format('DD MMMM YYYY')}
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

const xAxisFormatter = (label: number | string | undefined) =>
    isNumber(label) ? dayjs(label).format('MMM DD') : `${label}`;

export const TimeCreditConsumptionCard = (props: TimeCreditConsumptionCardProps): JSX.Element => {
    const ref = useRef(null);
    const unwrappedContainer = useUnwrapDOMRef(ref);

    const [timeChartProjectFilter, setTimeChartProjectFilter] = useState<Key | null>(null);

    const { useGetTransactionsAggregates } = useTransactionsQueries();
    const { useGetProjectNames } = useProjectActions();
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const fromDate = props.fromDate ? props.fromDate.valueOf() : undefined;
    const toDate = props.toDate ? props.toDate.valueOf() : undefined;
    const { data: transactionsData, isPending } = useGetTransactionsAggregates(
        { workspaceId, organizationId },
        {
            keys: new Set([TransactionsAggregatesKey.DATE, TransactionsAggregatesKey.SERVICE_NAME]),
            fromDate: fromDate?.toString(),
            toDate: toDate?.toString(),
            projectId: timeChartProjectFilter?.toString(),
        }
    );
    const { data: projectNamesData } = useGetProjectNames({ workspaceId, organizationId });
    const serviceNames = useMemo(() => getServiceNamesFromAggregates(transactionsData?.aggregates), [transactionsData]);
    const chartData = useMemo(
        () => convertAggregatesToTimeChartData(transactionsData?.aggregates, serviceNames),
        [transactionsData, serviceNames]
    );

    return (
        <View backgroundColor={'gray-100'} position={'relative'} minHeight={MIN_HEIGHT / 2} {...props} ref={ref}>
            <Flex justifyContent={'space-between'} UNSAFE_style={{ padding: dimensionValue('size-200') }}>
                <ComboBox
                    aria-label='Select a project'
                    defaultItems={orderBy(projectNamesData?.projects || [], ['name'])}
                    selectedKey={timeChartProjectFilter}
                    onSelectionChange={(selected) => setTimeChartProjectFilter(selected)}
                    id='time-credit-consumption-card-project-picker'
                    UNSAFE_className={classes.timeCreditConsumptionCardProjectPicker}
                >
                    {(item) => <Item>{item.name}</Item>}
                </ComboBox>
                {timeChartProjectFilter && (
                    <ActionButton
                        onPress={() => setTimeChartProjectFilter(null)}
                        aria-label='Clear project selection'
                        id='time-credit-consumption-card-project-picker-clear-button'
                        isQuiet
                    >
                        <Close />
                    </ActionButton>
                )}
                <DownloadSvgButton
                    text='Download'
                    fileName='Monthly consumption'
                    container={unwrappedContainer}
                    graphBackgroundColor='gray-100'
                    marginStart={'auto'}
                    id='time-credit-consumption-card-download-button'
                    isDisabled={isPending}
                />
            </Flex>
            {isPending ? (
                <View minHeight={MIN_HEIGHT}>
                    <Loading size='M' />
                </View>
            ) : isEmpty(chartData) ? (
                <Flex minHeight={MIN_HEIGHT} alignItems={'center'} justifyContent={'center'}>
                    <NotFound />
                </Flex>
            ) : (
                <ResponsiveContainer height={'100%'} width={'100%'} minHeight={MIN_HEIGHT}>
                    <DownloadableBarChart
                        title='Credit consumption by time'
                        data={chartData}
                        barSize={16}
                        margin={{ left: 16, right: 32, top: 16, bottom: 16 }}
                    >
                        <XAxis
                            type='number'
                            domain={[fromDate ?? 'auto', toDate ?? 'auto']}
                            dataKey='label'
                            axisLine={false}
                            tick={{ fontSize: 12 }}
                            tickFormatter={xAxisFormatter}
                        />
                        <YAxis type='number' axisLine={false} dx={-10} />
                        <Tooltip cursor={false} content={CustomTooltip} />
                        {serviceNames.map((serviceName) => (
                            <Bar
                                key={serviceName}
                                name={serviceName}
                                dataKey={`values.${serviceName}`}
                                stackId='a'
                                fill={getColorFromServiceName(serviceName)}
                                activeBar={
                                    <Rectangle
                                        fill={convertColorToFadedColor(getColorFromServiceName(serviceName), 50)}
                                    />
                                }
                            />
                        ))}
                    </DownloadableBarChart>
                </ResponsiveContainer>
            )}
        </View>
    );
};
