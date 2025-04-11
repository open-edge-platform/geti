// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen, waitFor } from '@testing-library/react';

import { GPUProvider } from '../../../../core/platform-utils/dto/utils.interface';
import { projectListRender as render } from '../../../../test-utils/projects-list-providers-render';
import { NewProjectDialogProvider } from '../../new-project-dialog-provider/new-project-dialog-provider.component';
import { DomainCardsMetadata } from './project-template.interface';
import { SingleTaskTemplate } from './single-task-template.component';
import { TABS_SINGLE_TEMPLATE } from './utils';

const mockGpuProvider = GPUProvider.NONE;
jest.mock('../../../../core/platform-utils/hooks/use-gpu-provider.hook', () => ({
    useGpuProvider: jest.fn(() => mockGpuProvider),
}));

describe('SingleTaskTemplate', () => {
    const tabToContent = [
        ['Detection', TABS_SINGLE_TEMPLATE.Detection],
        ['Segmentation', TABS_SINGLE_TEMPLATE.Segmentation],
        ['Classification', TABS_SINGLE_TEMPLATE.Classification],
        ['Anomaly', TABS_SINGLE_TEMPLATE.Anomaly],
    ];

    test.each(tabToContent)('renders correct subdomains for current tab', async (_tab, content) => {
        await render(
            <NewProjectDialogProvider>
                <SingleTaskTemplate setSelectedDomains={jest.fn} cards={content as DomainCardsMetadata[]} />
            </NewProjectDialogProvider>
        );

        await waitFor(() => {
            (content as DomainCardsMetadata[]).forEach((domainCard) => {
                expect(screen.getByTestId(domainCard.id)).toBeInTheDocument();
            });
        });
    });
});
