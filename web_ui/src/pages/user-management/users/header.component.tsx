// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useUsers } from '@geti/core/src/users/hook/use-users.hook';
import { Flex } from '@geti/ui';

import { useProductInfo } from '../../../core/platform-utils/hooks/use-platform-utils.hook';
import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { AddMemberPopup } from './add-member-popup/add-member-popup.component';
import { InviteUser } from './invite-user/invite-user.component';

export const Header = () => {
    const { useActiveUser } = useUsers();
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { data: activeUser } = useActiveUser(organizationId);

    const { data: productInfo } = useProductInfo();
    const isSaasEnvironment = useIsSaasEnv();

    const shouldShowAddUserButton = !isSaasEnvironment && productInfo.isSmtpDefined === false;
    const shouldShowInviteUserButton = isSaasEnvironment || productInfo.isSmtpDefined === true;

    const sendInviteId = 'send-invite-btn-id';

    if (activeUser === undefined) {
        return <></>;
    }

    return (
        <Flex justifyContent={'end'} alignItems={'center'} gap={'size-150'}>
            <>
                {shouldShowAddUserButton && (
                    <AddMemberPopup organizationId={organizationId} workspaceId={workspaceId} />
                )}

                {shouldShowInviteUserButton && (
                    <InviteUser
                        isAdmin={activeUser.isAdmin}
                        id={sendInviteId}
                        organizationId={organizationId}
                        workspaceId={workspaceId}
                    />
                )}
            </>
        </Flex>
    );
};
