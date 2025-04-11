// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { Screenshot } from '../../../camera-support/camera.interface';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { SidebarThumbnail } from './sidebar-thumbnail.component';

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

describe('SidebarThumbnail', () => {
    const mockedScreenshot = getMockedScreenshot({});

    const renderApp = async ({
        screenshots = [],
        defaultLabelId = '',
        isCloseSidebar = false,
        isLivePrediction = false,
        hasDefaultLabel = false,
    }: {
        screenshots?: Screenshot[];
        isCloseSidebar?: boolean;
        defaultLabelId?: string;
        isLivePrediction?: boolean;
        hasDefaultLabel?: boolean;
    }) => {
        const mockedProjectIdentifier = getMockedProjectIdentifier({});

        jest.mocked(useCameraParams).mockReturnValue({
            isLivePrediction,
            defaultLabelId,
            hasDefaultLabel,
            datasetId: 'data-id-test',
            isPhotoCaptureMode: true,
            projectId: mockedProjectIdentifier.projectId,
            workspaceId: mockedProjectIdentifier.workspaceId,
            organizationId: mockedProjectIdentifier.organizationId,
        });

        providersRender(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <SidebarThumbnail screenshots={screenshots} isCloseSidebar={isCloseSidebar} />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
    };

    it('empty screenshots', async () => {
        await renderApp({ isLivePrediction: true });
        await waitFor(() => {
            expect(screen.getByText('No media items available')).toBeVisible();
        });
    });

    it('unique screenshot', async () => {
        await renderApp({ screenshots: [mockedScreenshot], isLivePrediction: true });

        await waitFor(() => {
            expect(screen.getByRole('button', { name: 'open preview' })).toBeVisible();
        });
    });

    it('multiple screenshot', async () => {
        await renderApp({ screenshots: [mockedScreenshot] });

        expect(screen.getByRole('link', { name: 'View all captures' })).toBeVisible();
    });

    it('link includes default label', async () => {
        const defaultLabelId = '123321';
        await renderApp({ screenshots: [mockedScreenshot], hasDefaultLabel: true, defaultLabelId });

        expect(screen.getByRole('link', { name: 'View all captures' })).toHaveProperty(
            'href',
            expect.stringContaining(`defaultLabelId=${defaultLabelId}`)
        );
    });
});
