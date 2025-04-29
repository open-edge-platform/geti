// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import { RenderResult } from '@testing-library/react';

import { DatasetImportToNewProjectProvider } from '../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { ProjectsImportProvider } from '../providers/projects-import-provider/projects-import-provider.component';
import { CustomRenderOptions, providersRender } from './required-providers-render';

const customRender = async (ui: ReactElement, options?: CustomRenderOptions): Promise<RenderResult> => {
    const renderResult = await providersRender(
        <DatasetImportToNewProjectProvider>
            <ProjectsImportProvider>{ui}</ProjectsImportProvider>
        </DatasetImportToNewProjectProvider>,
        options
    );

    return renderResult;
};

export { customRender as projectListRender };
