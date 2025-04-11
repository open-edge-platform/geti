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

import { Divider, Flex } from '@adobe/react-spectrum';

import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { CreateWorkspace } from './create-workspace.component';
import { WorkspacesList } from './workspaces-list.component';

export const Workspaces = (): JSX.Element => {
    const { workspaces } = useWorkspaces();

    return (
        <Flex direction={'column'} height={'100%'} gap={'size-300'}>
            <HasPermission operations={[OPERATION.WORKSPACE_MANAGEMENT]}>
                <CreateWorkspace />
                <Divider size={'S'} />
            </HasPermission>
            <WorkspacesList workspaces={workspaces} />
        </Flex>
    );
};
