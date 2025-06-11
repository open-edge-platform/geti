// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex } from '@geti/ui';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { CreateWorkspace } from './create-workspace.component';
import { WorkspacesList } from './workspaces-list.component';

export const Workspaces = (): JSX.Element => {
    const { workspaces } = useWorkspaces();
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();

    return (
        <Flex direction={'column'} height={'100%'} gap={'size-300'}>
            <HasPermission
                operations={
                    FEATURE_FLAG_WORKSPACE_ACTIONS ? [OPERATION.WORKSPACE_CREATION] : [OPERATION.WORKSPACE_MANAGEMENT]
                }
            >
                <CreateWorkspace />
                <Divider size={'S'} />
            </HasPermission>
            <WorkspacesList workspaces={workspaces} />
        </Flex>
    );
};
