// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';

import { Edit, MoreMenu, PieChart } from '../../../../assets/icons';
import { CreditAccount } from '../../../../core/credits/credits.interface';
import { useCreditsQueries } from '../../../../core/credits/hooks/use-credits-api.hook';
import { MenuTrigger } from '../../../../shared/components/menu-trigger/menu-trigger.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { CreditAccountFormDialog } from '../dialogs/credit-account-form-dialog.component';
import { EditCreditAccountBalanceDialog } from '../dialogs/edit-balance-dialog.component';

interface ActionsCellProps {
    rowData: CreditAccount;
}

enum CreditAccountMenuActions {
    EDIT = 'Edit credit account',
    EDIT_BALANCE = 'Edit balance',
}

const menuItems = [CreditAccountMenuActions.EDIT, CreditAccountMenuActions.EDIT_BALANCE];

const renderItems = (item: string): JSX.Element => {
    return (
        <Flex gap={'size-75'} alignItems={'center'}>
            {item === CreditAccountMenuActions.EDIT && <Edit />}
            {item === CreditAccountMenuActions.EDIT_BALANCE && <PieChart />}
            <Text>{item}</Text>
        </Flex>
    );
};

export const ActionsCell = (props: ActionsCellProps): JSX.Element => {
    const { rowData: creditAccount } = props;
    const { useUpdateCreditAccountMutation, useUpdateCreditAccountBalanceMutation } = useCreditsQueries();
    const updateCreditAccount = useUpdateCreditAccountMutation();
    const updateCreditAccountBalance = useUpdateCreditAccountBalanceMutation();

    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [editBalanceDialogOpen, setEditBalanceDialogOpen] = useState(false);

    return (
        <>
            <MenuTrigger
                items={menuItems}
                id={`credit-account-menu-${creditAccount.id}`}
                onAction={(action) => {
                    if (action === CreditAccountMenuActions.EDIT.toLowerCase()) {
                        setEditDialogOpen(true);
                    } else if (action === CreditAccountMenuActions.EDIT_BALANCE.toLowerCase()) {
                        setEditBalanceDialogOpen(true);
                    }
                }}
                renderContent={renderItems}
            >
                <QuietActionButton>
                    <MoreMenu />
                </QuietActionButton>
            </MenuTrigger>
            <CreditAccountFormDialog
                creditAccount={creditAccount}
                isOpen={editDialogOpen}
                onOpenChange={(isOpen) => setEditDialogOpen(isOpen)}
                isLoading={updateCreditAccount.isPending}
                onSave={(newCreditAccount) => {
                    updateCreditAccount.mutate(
                        {
                            id: {
                                organizationId: creditAccount.organizationId,
                                creditAccountId: creditAccount.id,
                            },
                            newCreditAccount,
                        },
                        {
                            onSettled: () => setEditDialogOpen(false),
                        }
                    );
                }}
            />
            <EditCreditAccountBalanceDialog
                balance={creditAccount.balance}
                isOpen={editBalanceDialogOpen}
                onOpenChange={(isOpen) => setEditBalanceDialogOpen(isOpen)}
                isLoading={updateCreditAccountBalance.isPending}
                onSave={(balance) => {
                    updateCreditAccountBalance.mutate(
                        {
                            id: {
                                organizationId: creditAccount.organizationId,
                                creditAccountId: creditAccount.id,
                            },
                            balance,
                        },
                        {
                            onSettled: () => {
                                setEditBalanceDialogOpen(false);
                            },
                        }
                    );
                }}
            />
        </>
    );
};
