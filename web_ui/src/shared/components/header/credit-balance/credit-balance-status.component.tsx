// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Content, Dialog, DialogTrigger, Divider, Flex, Heading, ProgressCircle, Text, View } from '@geti/ui';
import { isEmpty, overSome } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { OrganizationBalance } from '../../../../core/credits/credits.interface';
import { useCreditsQueries } from '../../../../core/credits/hooks/use-credits-api.hook';
import { useTransactionsQueries } from '../../../../core/credits/transactions/hooks/use-transactions.hook';
import { paths } from '../../../../core/services/routes';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useFirstWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { formatDate, ONE_MINUTE } from '../../../utils';
import { CustomerSupportLink } from '../../customer-support-link/customer-support-link.component';
import { HasPermission } from '../../has-permission/has-permission.component';
import { OPERATION } from '../../has-permission/has-permission.interface';
import { Balance } from './balance.component';
import { CreditBalanceButton } from './credit-balance-button.component';
import { getClassServiceName, getProjectName, isBalanceLow } from './util';

import classes from './credit-balance.module.scss';

interface CreditBalanceStatusProps {
    isDarkMode: boolean;
}

const getClassOddRow = (index: number) => (index % 2 !== 0 ? classes.oddRow : '');
const isExhausted = (organizationBalance: OrganizationBalance | undefined) => organizationBalance?.available == 0;
const isLowOrExhausted = overSome([isBalanceLow, isExhausted]);

const RecentUsage = ({ close }: { close: () => void }) => {
    const navigate = useNavigate();

    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { useGetTransactions } = useTransactionsQueries();
    const { transactions, isPending } = useGetTransactions({ organizationId, workspaceId }, {});

    return (
        <>
            <Text>Recent credit usage</Text>

            <View UNSAFE_className={classes.creditUseContainer}>
                {isPending ? (
                    <Flex justifyContent='center' marginY={'size-100'}>
                        <ProgressCircle size='M' isIndeterminate aria-label='Loading' />
                    </Flex>
                ) : isEmpty(transactions) ? (
                    <Text UNSAFE_className={classes.emptyCredits}>Credit list is empty </Text>
                ) : (
                    transactions.map((transaction, index) => (
                        <Flex
                            gap={'size-115'}
                            alignItems={'center'}
                            key={`${transaction.millisecondsTimestamp}`}
                            UNSAFE_className={[classes.row, getClassOddRow(index)].join(' ')}
                        >
                            <View width={'20%'}>
                                <Text UNSAFE_className={getClassServiceName(transaction.serviceName)}>
                                    {transaction.serviceName}
                                </Text>
                            </View>
                            <Text width={'40%'} UNSAFE_className={classes.textEllipsis}>
                                {getProjectName(transaction)}
                            </Text>
                            <Text width={'20%'}>{transaction.credits} credits</Text>
                            <View width={'20%'}>
                                <Text UNSAFE_style={{ display: 'block' }}>
                                    {formatDate(transaction.millisecondsTimestamp, 'DD MMM YY')}
                                </Text>
                                <Text UNSAFE_className={classes.timeDate}>
                                    {formatDate(transaction.millisecondsTimestamp, 'HH:mm:ss')}
                                </Text>
                            </View>
                        </Flex>
                    ))
                )}
            </View>

            <Divider
                width={'100%'}
                height={'2px'}
                marginY={'size-200'}
                UNSAFE_style={{ background: 'var(--spectrum-global-color-gray-300)' }}
            />
            <Button
                variant={'primary'}
                onPress={() => {
                    close();
                    navigate(paths.account.usage({ organizationId }));
                }}
            >
                See usage details
            </Button>
        </>
    );
};

export const CreditBalanceStatus = ({ isDarkMode }: CreditBalanceStatusProps) => {
    const { organizationId } = useOrganizationIdentifier();
    const { useGetOrganizationBalanceQuery } = useCreditsQueries();

    const { data: organizationBalance, isPending: isOrganizationBalanceLoading } = useGetOrganizationBalanceQuery(
        { organizationId },
        { refetchInterval: ONE_MINUTE }
    );

    return (
        <DialogTrigger type='popover' hideArrow>
            <CreditBalanceButton isDarkMode={isDarkMode} />

            {(close) => (
                <Dialog width={'auto'} minWidth='size-6000'>
                    <Heading>
                        <Flex justifyContent={'space-between'} marginBottom={'size-150'}>
                            <Flex justifyContent={'space-between'} alignItems={'center'} gap={'size-225'}>
                                <Text>Credits remaining</Text>
                                {organizationBalance && isLowOrExhausted(organizationBalance) && (
                                    <Text
                                        UNSAFE_className={classes.creditExhausted}
                                        data-testid={'low-exhausted-warning'}
                                    >
                                        {isExhausted(organizationBalance) ? 'Exhausted' : 'Running out'}
                                    </Text>
                                )}
                            </Flex>

                            <CustomerSupportLink text={'Contact support'} className={classes.link} />
                        </Flex>

                        <Balance isLoading={isOrganizationBalanceLoading} organizationBalance={organizationBalance} />
                    </Heading>

                    <HasPermission operations={[OPERATION.CAN_VIEW_CREDITS_USAGE]}>
                        <Divider />

                        <Content>
                            <RecentUsage close={close} />
                        </Content>
                    </HasPermission>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
