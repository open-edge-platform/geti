// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import {
    AlertDialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Link,
    Text,
    Tooltip,
    TooltipTrigger,
    View,
    ViewProps,
} from '@adobe/react-spectrum';
import { Tooltip as ChartTooltip, Pie, PieChart, ResponsiveContainer, TooltipProps } from 'recharts';

import { CONTACT_SUPPORT } from '../../../core/const';
import { useCreditsQueries } from '../../../core/credits/hooks/use-credits-api.hook';
import { getBalanceUsedCredits } from '../../../core/credits/services/utils';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { ActionElement } from '../../../shared/components/action-element/action-element.component';
import { openNewTab, pluralize } from '../../../shared/utils';

import classes from './usage.module.scss';

const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
    if (active && payload && payload.length && (payload[0].name === 'Available' || payload[0].name === 'Blocked')) {
        return (
            <View backgroundColor={'gray-300'} padding={'size-250'}>
                <Heading level={6} margin={0} marginBottom={'size-50'}>
                    {payload[0].name}
                </Heading>
                <Text margin={0}>{pluralize(payload[0].payload.trueValue ?? 0, 'credit')}</Text>
            </View>
        );
    } else {
        return null;
    }
};

export const CreditConsumptionCard = (props: ViewProps<5>): JSX.Element => {
    const { organizationId } = useOrganizationIdentifier();
    const { useGetOrganizationBalanceQuery, useCreditsQuery } = useCreditsQueries();
    const { data: organizationBalance } = useGetOrganizationBalanceQuery({ organizationId });
    const {
        creditAccounts,
        status: creditAccountsLoadingStatus,
        isFetchingNextPage,
        getNextPage,
        hasNextPage,
    } = useCreditsQuery({ organizationId });

    useEffect(() => {
        if (hasNextPage && !isFetchingNextPage) getNextPage();
    }, [getNextPage, hasNextPage, isFetchingNextPage]);

    const totalRenewableCredits =
        creditAccountsLoadingStatus === 'success' && !isFetchingNextPage
            ? creditAccounts.reduce((acc, creditAccount) => acc + (creditAccount.renewableAmount ?? 0), 0)
            : 0;

    const availablePercentage = organizationBalance?.incoming
        ? Math.round((organizationBalance.available / organizationBalance.incoming) * 100)
        : 0;

    const pendingPercentage = organizationBalance?.incoming
        ? Math.round((organizationBalance.blocked / organizationBalance.incoming) * 100)
        : 0;

    const chartData = [
        {
            name: 'Available',
            value: availablePercentage,
            trueValue: organizationBalance?.available,
            fill: 'var(--energy-blue)',
            id: 'available',
        },
        {
            name: 'Pending',
            value: pendingPercentage,
            trueValue: organizationBalance?.blocked,
            fill: 'var(--spectrum-global-color-gray-800)',
            id: 'blocked',
        },
        {
            name: '',
            value: 100 - availablePercentage - pendingPercentage,
            trueValue: organizationBalance && getBalanceUsedCredits(organizationBalance),
            fill: 'transparent',
            id: 'placeholder',
        },
    ];

    return (
        <View {...props} paddingX={'size-200'} paddingBottom={'size-200'} backgroundColor={'gray-200'}>
            <Flex gap={'size-100'} justifyContent={'space-between'} alignItems={'baseline'}>
                <Heading>Credit limit</Heading>
                <DialogTrigger>
                    <Link>More credits</Link>
                    <AlertDialog
                        title='More credits'
                        primaryActionLabel='Contact support'
                        onPrimaryAction={() => openNewTab(CONTACT_SUPPORT)}
                        cancelLabel='Close'
                    >
                        Looking for more credits? Reach out to our Customer Support team to inquire about the
                        possibilities.
                    </AlertDialog>
                </DialogTrigger>
            </Flex>
            <Divider marginBottom={'size-150'} size='S' />
            <Text
                UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}
                data-testid='credits-limit-card-renewable-credits-text'
            >
                Monthly renewal of {totalRenewableCredits} credits
            </Text>
            <View height={'size-3000'}>
                <ResponsiveContainer height={240}>
                    <PieChart width={180} height={180}>
                        <ChartTooltip wrapperStyle={{ zIndex: 2 }} content={<CustomTooltip />} />
                        <Pie
                            data={[{ name: '', value: 100, fill: 'var(--spectrum-global-color-gray-300)' }]}
                            dataKey='value'
                            innerRadius={80}
                            outerRadius={100}
                            stroke='none'
                            isAnimationActive={false}
                            tooltipType='none'
                        />
                        <Pie
                            data={chartData}
                            dataKey='value'
                            startAngle={90}
                            endAngle={-270}
                            outerRadius={100}
                            innerRadius={80}
                            stroke='none'
                        />
                    </PieChart>
                </ResponsiveContainer>
                <View position={'relative'} top={'-147px'} UNSAFE_style={{ textAlign: 'center' }}>
                    <Text
                        UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-500)' }}
                        data-testid='credits-limit-card-available-credits-chart-label-text'
                    >
                        {organizationBalance?.available}
                    </Text>
                    <br />
                    <Text
                        UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}
                        data-testid='credits-limit-card-total-credits-chart-label-text'
                    >
                        of {organizationBalance?.incoming ?? 0}
                    </Text>
                </View>
            </View>
            <Flex justifyContent={'space-between'} UNSAFE_className={classes.creditsCardLegendContainer}>
                <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }} alignSelf='end'>
                    1 credit = 1 image training
                </Text>
                <View paddingTop={!pendingPercentage ? 'size-200' : 'size-0'}>
                    <TooltipTrigger>
                        <ActionElement>
                            <Flex alignItems={'center'} gap={'size-50'} isHidden={!pendingPercentage}>
                                <View
                                    width={'size-100'}
                                    height={'size-100'}
                                    UNSAFE_style={{
                                        borderRadius: 'var(--spectrum-global-dimension-size-25)',
                                        backgroundColor: 'var(--spectrum-global-color-gray-800)',
                                    }}
                                />
                                <Text
                                    UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}
                                    data-testid='credits-limit-card-chart-legend-pending-credits-text'
                                >
                                    {pendingPercentage}%
                                </Text>
                            </Flex>
                        </ActionElement>
                        <Tooltip>Pending credits</Tooltip>
                    </TooltipTrigger>
                    <TooltipTrigger>
                        <ActionElement>
                            <Flex alignItems={'center'} gap={'size-50'}>
                                <View
                                    width={'size-100'}
                                    height={'size-100'}
                                    UNSAFE_style={{
                                        borderRadius: 'var(--spectrum-global-dimension-size-25)',
                                        backgroundColor: 'var(--energy-blue)',
                                    }}
                                />
                                <Text
                                    UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}
                                    data-testid='credits-limit-card-chart-legend-available-credits-text'
                                >
                                    {availablePercentage}%
                                </Text>
                            </Flex>
                        </ActionElement>
                        <Tooltip>Available credits</Tooltip>
                    </TooltipTrigger>
                </View>
            </Flex>
        </View>
    );
};
