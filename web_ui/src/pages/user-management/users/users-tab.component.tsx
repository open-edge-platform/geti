// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, useState } from 'react';

import { Flex } from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';
import { useNavigate } from 'react-router-dom';

import { paths } from '../../../core/services/routes';
import { User } from '../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { PageLayoutWithTabs } from '../../../shared/components/page-layout/page-layout-with-tabs.component';
import { TabItem } from '../../../shared/components/tabs/tabs.interface';
import { Header } from './header.component';
import { WorkspaceUsersPanel } from './workspace-users-panel.component';
import { WorkspaceUsers } from './workspace-users/workspace-users.component';

enum UsersTabs {
    DETAILS = 'details',
}

const USERS_TABS_TO_PATH_MAPPING = {
    [UsersTabs.DETAILS]: paths.account.users.details,
};

interface UsersTabProps {
    activeUser: User | undefined;
}

export const UsersTab = ({ activeUser }: UsersTabProps): JSX.Element => {
    const { organizationId } = useOrganizationIdentifier();
    const [selectedWorkspace, setSelectedWorkspace] = useState<string>();

    const activeTab = UsersTabs.DETAILS;
    const navigate = useNavigate();

    const handleTabChange = (key: Key): void => {
        if (key === activeTab) {
            return;
        }

        navigate(USERS_TABS_TO_PATH_MAPPING[key as UsersTabs]({ organizationId }));
    };

    if (activeUser === undefined) {
        return <></>;
    }

    const tabs: TabItem[] = [
        {
            id: `${UsersTabs}-tab-id`,
            key: UsersTabs.DETAILS,
            name: capitalize(UsersTabs.DETAILS),
            children: (
                <WorkspaceUsers
                    activeUser={activeUser}
                    workspaceId={selectedWorkspace === '' ? undefined : selectedWorkspace}
                />
            ),
        },
    ];

    return (
        <Flex direction={'column'} height={'100%'}>
            <Flex justifyContent={'space-between'} marginBottom={'size-200'}>
                <WorkspaceUsersPanel
                    selectedWorkspace={selectedWorkspace}
                    setSelectedWorkspace={setSelectedWorkspace}
                />
                <HasPermission operations={[OPERATION.MANAGE_USER, OPERATION.INVITE_USER]}>
                    <Header />
                </HasPermission>
            </Flex>
            <Flex direction={'column'} flex={1}>
                <PageLayoutWithTabs
                    activeTab={activeTab}
                    tabs={tabs}
                    tabsLabel={'Users tabs'}
                    onSelectionChange={handleTabChange}
                />
            </Flex>
        </Flex>
    );
};
