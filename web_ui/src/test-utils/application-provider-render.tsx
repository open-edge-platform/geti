// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import { RenderResult, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { CustomRenderOptions, providersRender } from './required-providers-render';

// TODO: Remove this customRender
const customRender = async (ui: ReactElement, options?: CustomRenderOptions): Promise<RenderResult> => {
    const render = providersRender(ui, options);

    const progressBar = screen.queryByRole('progressbar', { name: 'Loading' });
    if (progressBar) {
        await waitForElementToBeRemoved(progressBar);
    }

    return render;
};

export { customRender as applicationRender };
