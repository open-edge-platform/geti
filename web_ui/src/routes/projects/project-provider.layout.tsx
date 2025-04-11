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
