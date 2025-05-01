// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { MenuTrigger } from '@shared/components/menu-trigger/menu-trigger.component';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';

import { Edit, MoreMenu } from '../../../../assets/icons';
import { useSubscriptions } from '../../../../core/credits/subscriptions/hooks/use-subscription-api.hook';
import { Quota } from '../../../../core/credits/subscriptions/quotas.interface';
import { EditServiceLimitDialog } from '../dialogs/edit-service-limit-dialog.component';

interface ActionCellProps {
    rowData: Quota;
}

enum ServiceLimitsMenuActions {
    EDIT = 'Edit service limit',
}

const menuItems = [ServiceLimitsMenuActions.EDIT];

const renderItems = (item: string): JSX.Element => {
    return (
        <Flex gap={'size-75'} alignItems={'center'}>
            <Edit />
            <Text>{item}</Text>
        </Flex>
    );
};

export const ActionCell = (props: ActionCellProps): JSX.Element => {
    const { rowData: quota } = props;
    const { useUpdateQuotaMutation } = useSubscriptions();
    const updateQuota = useUpdateQuotaMutation();

    const [editDialogOpen, setEditDialogOpen] = useState(false);

    const handleUpdateQuota = (newQuota: Quota) => {
        updateQuota.mutate(newQuota, {
            onSuccess: () => {
                setEditDialogOpen(false);
            },
        });
    };

    return (
        <>
            <MenuTrigger
                items={menuItems}
                id={`service-limit-menu-${quota.id}`}
                onAction={(action) => {
                    if (action === ServiceLimitsMenuActions.EDIT.toLowerCase()) {
                        setEditDialogOpen(true);
                    }
                }}
                renderContent={renderItems}
            >
                <QuietActionButton>
                    <MoreMenu />
                </QuietActionButton>
            </MenuTrigger>
            <EditServiceLimitDialog
                quota={quota}
                onSave={handleUpdateQuota}
                isOpen={editDialogOpen}
                isLoading={updateQuota.isPending}
                onOpenChange={setEditDialogOpen}
            />
        </>
    );
};
