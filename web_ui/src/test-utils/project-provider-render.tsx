// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { ProjectProvider } from '../pages/project-details/providers/project-provider/project-provider.component';
import { getMockedProjectIdentifier } from './mocked-items-factory/mocked-identifiers';
import { CustomRenderOptions, providersRender } from './required-providers-render';

const customRender = async (ui: ReactElement, options?: CustomRenderOptions) => {
    const projectsProvider = <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>{ui}</ProjectProvider>;
    const render = providersRender(projectsProvider, options);

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return render;
};

export { customRender as projectRender };
