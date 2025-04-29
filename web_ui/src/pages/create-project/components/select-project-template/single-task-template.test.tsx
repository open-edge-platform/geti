// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
