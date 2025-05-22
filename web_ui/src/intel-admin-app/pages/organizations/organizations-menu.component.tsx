// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { ActionButton, Flex, Text } from '@geti/ui';
import { Delete, MoreMenu, Pause, Play } from '@geti/ui/icons';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { useOrganizationsApi } from '../../../core/organizations/hook/use-organizations-api.hook';
import { AccountStatus, Organization } from '../../../core/organizations/organizations.interface';
import { DeleteDialog } from '../../../shared/components/delete-dialog/delete-dialog.component';
import { MenuTrigger } from '../../../shared/components/menu-trigger/menu-trigger.component';
import { getItemActions, OrganizationsMenuItems } from './utils';

interface OrganizationsMenuProps {
    organization: Organization;
}

export const OrganizationsMenu = ({ organization }: OrganizationsMenuProps): JSX.Element => {
    const actionItems = getItemActions(organization.status);
    const { useUpdateOrganizationMutation } = useOrganizationsApi();
    const updateOrganization = useUpdateOrganizationMutation();

    const deleteTriggerState = useOverlayTriggerState({});

    const handleUpdateOrganization = (status: AccountStatus): void => {
        updateOrganization.mutate({ ...organization, status });
    };

    const handleDeleteOrganization = (): void => {
        handleUpdateOrganization(AccountStatus.DELETED);
    };

    const handleOnAction = (key: Key): void => {
        if (key === OrganizationsMenuItems.DELETE.toLocaleLowerCase()) {
            deleteTriggerState.open();
        } else if (key === OrganizationsMenuItems.SUSPEND.toLocaleLowerCase()) {
            handleUpdateOrganization(AccountStatus.SUSPENDED);
        } else if (key === OrganizationsMenuItems.ACTIVATE.toLocaleLowerCase()) {
            handleUpdateOrganization(AccountStatus.ACTIVATED);
        }
    };

    const renderItem = (item: string): JSX.Element => {
        return (
            <Flex alignItems={'center'} gap={'size-50'}>
                {item === OrganizationsMenuItems.DELETE ? (
                    <Delete />
                ) : item === OrganizationsMenuItems.ACTIVATE ? (
                    <Play />
                ) : (
                    <Pause />
                )}
                <Text>{item}</Text>
            </Flex>
        );
    };

    if (!actionItems.length) {
        return <></>;
    }

    return (
        <>
            <MenuTrigger
                id={`organizations-menu-${organization.id}-id`}
                items={actionItems}
                ariaLabel={organization.name}
                onAction={handleOnAction}
                renderContent={renderItem}
            >
                <ActionButton
                    isQuiet
                    aria-label={`${organization.name} menu button`}
                    id={`organizations-menu-${organization.name}-button`}
                >
                    <MoreMenu />
                </ActionButton>
            </MenuTrigger>
            <DeleteDialog
                title={'organization'}
                name={organization.name}
                onAction={handleDeleteOrganization}
                triggerState={deleteTriggerState}
            />
        </>
    );
};
