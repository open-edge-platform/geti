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

import { screen, waitFor } from '@testing-library/react';

import '@testing-library/jest-dom/extend-expect';

import { Label } from '../../../../core/labels/label.interface';
import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { Screenshot } from '../../../camera-support/camera.interface';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { DeviceSettingsProvider } from '../../providers/device-settings-provider.component';
import { OpenSidebar } from './open-sidebar.component';

jest.mock('../../../camera-support/use-camera.hook', () => ({
    useCamera: jest.fn(() => ({
        availableDevices: [],
        handleGetMediaDevices: jest.fn(),
    })),
}));

jest.mock('../../../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../../../shared/navigator-utils'),
    getVideoDevices: jest.fn().mockResolvedValue([]),
}));

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

jest.mock('@react-aria/utils', () => ({
    ...jest.requireActual('@react-aria/utils'),
    isWebKit: jest.fn(() => false),
}));

describe('OpenSidebar', () => {
    const mockedLabel = getMockedLabel({ name: 'label-one' });
    const mockedScreenshotOne = getMockedScreenshot({ id: 'id-test-1', labelIds: [mockedLabel.id] });
    const mockedScreenshotTwo = getMockedScreenshot({ id: 'id-test-2', labelIds: [mockedLabel.id] });
    const mockedScreenshotThree = getMockedScreenshot({ id: 'id-test-3' });

    const renderApp = ({
        labels = [],
        screenshots = [],
        isLivePrediction = false,
    }: {
        labels?: Label[];
        screenshots?: Screenshot[];
        isLivePrediction?: boolean;
    }) => {
        const mockedProjectIdentifier = getMockedProjectIdentifier({});

        jest.mocked(useCameraParams).mockReturnValue({
            isLivePrediction,
            defaultLabelId: '',
            hasDefaultLabel: false,
            datasetId: 'data-id-test',
            isPhotoCaptureMode: true,
            projectId: mockedProjectIdentifier.projectId,
            workspaceId: mockedProjectIdentifier.workspaceId,
            organizationId: mockedProjectIdentifier.organizationId,
        });

        providersRender(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <DeviceSettingsProvider>
                    <OpenSidebar labels={labels} screenshots={screenshots} isLivePrediction={isLivePrediction} />
                </DeviceSettingsProvider>
            </ProjectProvider>
        );
    };

    it('unique screenshot mode', async () => {
        renderApp({ screenshots: [mockedScreenshotOne, mockedScreenshotTwo], isLivePrediction: true });

        await waitFor(() => {
            expect(screen.getByText('Camera Settings')).toBeVisible();
            expect(screen.getByRole('button', { name: 'open preview' })).toBeVisible();
        });
    });

    it('shows total labeled images ', async () => {
        const unlabeledScreenshots = [mockedScreenshotThree];
        const labeledScreenshots = [mockedScreenshotOne, mockedScreenshotTwo];
        const screenshots = [...unlabeledScreenshots, ...labeledScreenshots];

        renderApp({
            labels: [mockedLabel],
            screenshots,
            isLivePrediction: false,
        });

        await waitFor(() => {
            expect(screen.getByRole('meter')).toHaveTextContent(`${mockedLabel.name}${labeledScreenshots.length}`);
        });
    });
});
