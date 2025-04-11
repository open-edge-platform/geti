// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';

import { usePlatformUtils } from '../../../core/platform-utils/hooks/use-platform-utils.hook';
import { useUsers } from '../../../core/users/hook/use-users.hook';
import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { AddMemberPopup } from './add-member-popup/add-member-popup.component';
import { InviteUser } from './invite-user/invite-user.component';

export const Header = () => {
    const { useActiveUser } = useUsers();
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { data: activeUser } = useActiveUser(organizationId);

    const { useProductInfo } = usePlatformUtils();
    const { data: productInfo } = useProductInfo();
    const isSaasEnvironment = useIsSaasEnv();

    const shouldShowAddUserButton = !isSaasEnvironment && productInfo?.isSmtpDefined === false;
    const shouldShowInviteUserButton = isSaasEnvironment || productInfo?.isSmtpDefined === true;

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
