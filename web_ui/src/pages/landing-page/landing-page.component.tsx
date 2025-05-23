// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DatasetImportToNewProjectProvider } from '../../features/dataset-import/providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { WorkspacesTabs } from './workspaces-tabs/workspaces-tabs.component';

const WorkspaceScreen = () => {
    return (
        <DatasetImportToNewProjectProvider>
            <WorkspacesTabs />
        </DatasetImportToNewProjectProvider>
    );
};

export default WorkspaceScreen;
