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
