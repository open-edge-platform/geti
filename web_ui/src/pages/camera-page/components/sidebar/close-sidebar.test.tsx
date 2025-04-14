// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { Screenshot } from '../../../camera-support/camera.interface';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { CloseSidebar } from './close-sidebar.component';

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

describe('CloseSidebar', () => {
    const mockedScreenshot = getMockedScreenshot({});

    const renderApp = async ({
        screenshots = [],
        isLivePrediction = false,
    }: {
        screenshots?: Screenshot[];
        isLivePrediction?: boolean;
    }) => {
        const mockedProjectIdentifier = getMockedProjectIdentifier({});

        jest.mocked(useCameraParams).mockReturnValue(
            getUseCameraParams({
                isLivePrediction,
                projectId: mockedProjectIdentifier.projectId,
                workspaceId: mockedProjectIdentifier.workspaceId,
                organizationId: mockedProjectIdentifier.organizationId,
            })
        );

        providersRender(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <CloseSidebar screenshots={screenshots} isLivePrediction={isLivePrediction} />
            </ProjectProvider>
        );
        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
    };

    it('unique screenshot mode', async () => {
        await renderApp({ screenshots: [mockedScreenshot], isLivePrediction: true });

        expect(screen.getByRole('button', { name: 'open preview' })).toBeVisible();
    });

    it('unique screenshot mode false', async () => {
        const screenshots = [
            { ...mockedScreenshot, id: '123' },
            { ...mockedScreenshot, id: '321' },
        ];

        await renderApp({ screenshots, isLivePrediction: false });

        expect(screen.getByText(screenshots.length)).toBeVisible();
        expect(screen.queryByRole('button', { name: 'open preview' })).not.toBeInTheDocument();
    });
});
