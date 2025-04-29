// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
