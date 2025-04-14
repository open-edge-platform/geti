// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Grid, repeat } from '@adobe/react-spectrum';

import { WorkspaceEntity } from '../../../core/workspaces/services/workspaces.interface';
import { WorkspaceCard } from './workspace-card.component';

interface WorkspacesListProps {
    workspaces: WorkspaceEntity[];
}

export const WorkspacesList = ({ workspaces }: WorkspacesListProps): JSX.Element => {
    return (
        <Grid
            columns={repeat('auto-fit', 'size-3400')}
            autoRows={'size-1700'}
            gap={'size-300'}
            UNSAFE_style={{ overflowY: 'auto' }}
            alignItems={'center'}
            flex={1}
        >
            {workspaces.map((workspace) => (
                <WorkspaceCard key={workspace.id} workspace={workspace} workspaces={workspaces} />
            ))}
        </Grid>
    );
};
