// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';
import { Grid, repeat } from '@geti/ui';

import { useDefaultWorkspace } from '../../landing-page/workspaces-tabs/use-default-workspace.hook';
import { WorkspaceCard } from './workspace-card.component';

interface WorkspacesListProps {
    workspaces: WorkspaceEntity[];
}

export const WorkspacesList = ({ workspaces }: WorkspacesListProps): JSX.Element => {
    const { defaultWorkspaceId, reorderedWorkspaces } = useDefaultWorkspace(workspaces);

    return (
        <Grid
            columns={repeat('auto-fit', 'size-3400')}
            autoRows={'size-1700'}
            gap={'size-300'}
            UNSAFE_style={{ overflowY: 'auto' }}
            alignItems={'center'}
            flex={1}
        >
            {reorderedWorkspaces.map((workspace) => (
                <WorkspaceCard
                    key={workspace.id}
                    workspace={workspace}
                    workspaces={reorderedWorkspaces}
                    isDefaultWorkspace={defaultWorkspaceId === workspace.id}
                />
            ))}
        </Grid>
    );
};
