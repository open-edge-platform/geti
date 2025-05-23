// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { paths } from '@geti/core';
import { Button, Flex, Loading, Skeleton, Text, View } from '@geti/ui';
import { Navigate } from 'react-router-dom';

import { NewCreditAccount } from '../../../core/credits/credits.interface';
import { useCreditsQueries } from '../../../core/credits/hooks/use-credits-api.hook';
import { useSubscriptions } from '../../../core/credits/subscriptions/hooks/use-subscription-api.hook';
import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Header } from '../../shared/components/header/header.component';
import { CreditAccountFormDialog } from './dialogs/credit-account-form-dialog.component';
import { useOrganization } from './hooks/organization.hook';
import { CreditAccountsTable } from './organization-credit-accounts-table.component';

import classes from './organization.module.scss';

export const OrganizationCreditAccounts = (): JSX.Element => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { organizationId } = useOrganization();
    const { useGetOrganizationBalanceQuery, useCreditsQuery, useCreateCreditAccountMutation } = useCreditsQueries();
    const { useGetActiveSubscriptionQuery } = useSubscriptions();
    const createCreditAccount = useCreateCreditAccountMutation();
    const { status: subscriptionStatus, isLoading: isSubscriptionLoading } = useGetActiveSubscriptionQuery({
        organizationId,
    });

    const { data: balance, isLoading: isBalanceLoading } = useGetOrganizationBalanceQuery(
        { organizationId },
        { enabled: subscriptionStatus === 'success' }
    );
    const { creditAccounts, isLoading, isFetchingNextPage, getNextPage } = useCreditsQuery(
        { organizationId },
        { enabled: subscriptionStatus === 'success' }
    );

    const [createCreditAccountDialogIsOpen, setCreateCreditAccountDialogIsOpen] = useState(false);

    if (!FEATURE_FLAG_CREDIT_SYSTEM) {
        return <Navigate to={paths.intelAdmin.index({})} />;
    }

    const onSave = (creditAccount: NewCreditAccount) => {
        createCreditAccount.mutate(creditAccount, { onSettled: () => setCreateCreditAccountDialogIsOpen(false) });
    };

    return (
        <>
            <Header title={'Credit accounts'} />

            {isSubscriptionLoading ? (
                <View paddingBottom={'size-300'}>
                    <Loading />
                </View>
            ) : subscriptionStatus === 'error' ? (
                <View paddingBottom={'size-300'}>
                    <Text>Organization hasn&apos;t subscribed yet to any Intel Geti products.</Text>
                </View>
            ) : (
                <>
                    <View paddingBottom={'size-300'}>
                        <Flex justifyContent={'space-between'} alignItems={'center'}>
                            <View>
                                <Text>Total available credit</Text>
                                <br />
                                {isBalanceLoading ? (
                                    <Skeleton
                                        width={'size-1600'}
                                        height={'size-400'}
                                        UNSAFE_className={classes.organizationBalanceTextSkeleton}
                                    />
                                ) : (
                                    <Text
                                        data-testid='organization-balance-value'
                                        id='organization-balance-value'
                                        UNSAFE_className={classes.organizationBalanceText}
                                    >
                                        {balance?.available}
                                    </Text>
                                )}
                            </View>
                            <Button
                                variant='accent'
                                id='add-credits-button'
                                onPress={() => setCreateCreditAccountDialogIsOpen(true)}
                            >
                                Add credits
                            </Button>
                        </Flex>
                    </View>
                    <View>
                        <CreditAccountsTable
                            creditAccounts={creditAccounts}
                            isLoading={isLoading}
                            isLoadingNextPage={isFetchingNextPage}
                            getNextPage={getNextPage}
                        />
                    </View>
                    <CreditAccountFormDialog
                        isOpen={createCreditAccountDialogIsOpen}
                        onOpenChange={setCreateCreditAccountDialogIsOpen}
                        onSave={onSave}
                        isLoading={createCreditAccount.isPending}
                        isNew
                    />
                </>
            )}
        </>
    );
};
