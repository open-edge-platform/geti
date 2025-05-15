// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Button } from '@geti/ui';
import { capitalize } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../core/services/routes';
import { useUsers } from '../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE, User, USER_ROLE } from '../../core/users/users.interface';
import { useHandleSignOut } from '../../hooks/use-handle-sign-out/use-handle-sign-out.hook';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useOrganizationIdentifier } from '../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useMediaUpload } from '../../providers/media-upload-provider/media-upload-provider.component';
import { useFirstWorkspaceIdentifier } from '../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { useCheckPermission } from '../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../shared/components/has-permission/has-permission.interface';
import { Loading } from '../../shared/components/loading/loading.component';
import { PageLayoutWithTabs } from '../../shared/components/page-layout/page-layout-with-tabs.component';
import { ShowForOnPrem } from '../../shared/components/show-for-onprem/show-for-onprem.component';
import { TabItem } from '../../shared/components/tabs/tabs.interface';
import { useActiveTab } from '../../shared/hooks/use-active-tab.hook';
import { Analytics as AnalyticsPage } from '../analytics/analytics.component';
import { PersonalAccessTokenPage } from './personal-access-token-page/personal-access-token-page.component';
import { ProfilePage } from './profile-page/profile-page.component';
import { SignOutWarningDialog } from './profile-page/sign-out-warning-dialog.component';
import { SecurityPage } from './security-page/security-page.component';
import { Storage } from './storage/storage.component';
import { Usage } from './usage/usage.component';
import { UsersTab } from './users/users-tab.component';
import { Workspaces } from './workspaces/workspaces.component';

export enum UserManagementTabs {
    PROFILE = 'profile',
    WORKSPACES = 'workspaces',
    USERS = 'users',
    PERSONAL_ACCESS_TOKEN = 'personal-access-token',
    SECURITY = 'security',
    ANALYTICS = 'analytics',
    STORAGE = 'storage',
    USAGE = 'usage',
}

const USER_MANAGEMENT_TABS_TO_PATH = {
    [UserManagementTabs.PROFILE]: paths.account.profile,
    [UserManagementTabs.WORKSPACES]: paths.account.workspaces,
    [UserManagementTabs.USERS]: paths.account.users.index,
    [UserManagementTabs.PERSONAL_ACCESS_TOKEN]: paths.account.personalAccessToken,
    [UserManagementTabs.SECURITY]: paths.account.security,
    [UserManagementTabs.ANALYTICS]: paths.account.analytics,
    [UserManagementTabs.STORAGE]: paths.account.storage,
    [UserManagementTabs.USAGE]: paths.account.usage,
};

const useDecorateCheckPermission = (operations: OPERATION[]) => {
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { useActiveUser } = useUsers();

    const { data: activeUser } = useActiveUser(organizationId);

    const shouldShowUsageTab = useCheckPermission(operations);

    if (shouldShowUsageTab) {
        return true;
    }

    // TODO: Remove this ugly hack once we have a proper design for the account page
    // Currently the issue is that we cannot rely only on useCheckPermission hook because when the user is on the
    // account page, we have no idea what is the currently selected workspace. In the future we should either move
    // Usage tab to other place or move the whole account tab to be under workspaces,
    // i.e. /organizations/:organizationId/workspaces/:workspaceId/account
    const isWorkspaceAdmin = activeUser?.roles.some(
        (role) =>
            role.role === USER_ROLE.WORKSPACE_ADMIN &&
            role.resourceId === workspaceId &&
            role.resourceType === RESOURCE_TYPE.WORKSPACE
    );

    return isWorkspaceAdmin;
};

export const UserManagement = (): JSX.Element => {
    const handleSignOut = useHandleSignOut();
    const { organizationId } = useOrganizationIdentifier();
    const { isUploadInProgress } = useMediaUpload();
    const { useActiveUser } = useUsers();
    const { data: activeUser } = useActiveUser(organizationId);
    const navigate = useNavigate();
    const { FEATURE_FLAG_WORKSPACE_ACTIONS, FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const isSaasEnvironment = useIsSaasEnv();
    const shouldShowUsageTab = useDecorateCheckPermission([OPERATION.USAGE_TAB]) && FEATURE_FLAG_CREDIT_SYSTEM;
    const shouldShowAnalyticsTab = useDecorateCheckPermission([OPERATION.ANALYTICS_TAB]) && !isSaasEnvironment;

    const activeTab = useActiveTab(UserManagementTabs.PROFILE);

    const onSelectionChangeHandler = (key: Key) => {
        if (key === activeTab) {
            return;
        }

        navigate(USER_MANAGEMENT_TABS_TO_PATH[key as UserManagementTabs]({ organizationId }));
    };

    if (activeUser === undefined) {
        return <Loading />;
    }

    const actions = isUploadInProgress ? (
        <SignOutWarningDialog
            handleSignOut={handleSignOut}
            button={
                <Button variant='primary' id='sign-out-button-id' UNSAFE_style={{ whiteSpace: 'nowrap' }}>
                    Sign out
                </Button>
            }
        />
    ) : (
        <Button
            variant='primary'
            onPress={handleSignOut}
            id='sign-out-button-id'
            UNSAFE_style={{ width: 'max-content' }}
        >
            Sign out
        </Button>
    );

    const getItems = () => {
        const TABS: TabItem[] = [
            {
                id: `${UserManagementTabs.PROFILE}-user-page`,
                key: UserManagementTabs.PROFILE,
                name: capitalize(UserManagementTabs.PROFILE),
                children: (
                    <ProfilePage
                        activeUser={activeUser as User}
                        organizationId={organizationId}
                        isSaaSEnv={isSaasEnvironment}
                    />
                ),
            },
            {
                id: `${UserManagementTabs.WORKSPACES}-user-page`,
                key: UserManagementTabs.WORKSPACES,
                name: capitalize(UserManagementTabs.WORKSPACES),
                children: <Workspaces />,
            },
            {
                id: `${UserManagementTabs.USERS}-user-page`,
                key: UserManagementTabs.USERS,
                name: capitalize(UserManagementTabs.USERS),
                children: <UsersTab activeUser={activeUser as User} />,
            },
            {
                id: `${UserManagementTabs.PERSONAL_ACCESS_TOKEN}-user-page`,
                key: UserManagementTabs.PERSONAL_ACCESS_TOKEN,
                name: 'Token',
                children: <PersonalAccessTokenPage activeUserId={activeUser.id} organizationId={organizationId} />,
            },
            {
                id: `${UserManagementTabs.SECURITY}-user-page`,
                key: UserManagementTabs.SECURITY,
                name: capitalize(UserManagementTabs.SECURITY),
                children: <SecurityPage activeUserId={activeUser.id} />,
            },
            {
                id: `${UserManagementTabs.ANALYTICS}-user-page`,
                key: UserManagementTabs.ANALYTICS,
                name: capitalize(UserManagementTabs.ANALYTICS),
                children: (
                    <ShowForOnPrem>
                        <AnalyticsPage />
                    </ShowForOnPrem>
                ),
            },
            {
                id: `${UserManagementTabs.STORAGE}-user-page`,
                key: UserManagementTabs.STORAGE,
                name: capitalize(UserManagementTabs.STORAGE),
                children: (
                    <ShowForOnPrem>
                        <Storage />
                    </ShowForOnPrem>
                ),
            },
            {
                id: `${UserManagementTabs.USAGE}-user-page`,
                key: UserManagementTabs.USAGE,
                name: capitalize(UserManagementTabs.USAGE),
                children: <Usage />,
            },
        ];

        const filteredItems: Partial<Record<UserManagementTabs, boolean>> = {
            [UserManagementTabs.ANALYTICS]: shouldShowAnalyticsTab,
            [UserManagementTabs.STORAGE]: !isSaasEnvironment,
            [UserManagementTabs.WORKSPACES]: FEATURE_FLAG_WORKSPACE_ACTIONS,
            [UserManagementTabs.USAGE]: shouldShowUsageTab,
        };

        return TABS.filter(({ key }) => (key in filteredItems ? filteredItems[key as UserManagementTabs] : true));
    };

    return (
        <PageLayoutWithTabs
            actionButton={actions}
            tabs={getItems()}
            tabsLabel={'User profile'}
            onSelectionChange={onSelectionChangeHandler}
            activeTab={activeTab}
            tabContentTopMargin={'size-300'}
        />
    );
};
