// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Outlet } from 'react-router-dom';

import { useProjectIdentifier } from '../../hooks/use-project-identifier/use-project-identifier';
import { ProjectProvider } from '../../pages/project-details/providers/project-provider/project-provider.component';

export const ProjectProviderLayout = (): JSX.Element => {
    const { workspaceId, projectId, organizationId } = useProjectIdentifier();

    return (
        <ProjectProvider projectIdentifier={{ workspaceId, projectId, organizationId }}>
            <Outlet />
        </ProjectProvider>
    );
};
