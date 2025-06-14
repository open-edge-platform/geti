// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

    const renderApp = ({ labels = [], screenshots = [] }: { labels?: Label[]; screenshots?: Screenshot[] }) => {
        const mockedProjectIdentifier = getMockedProjectIdentifier({});

        jest.mocked(useCameraParams).mockReturnValue({
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
                    <OpenSidebar labels={labels} screenshots={screenshots} />
                </DeviceSettingsProvider>
            </ProjectProvider>
        );
    };

    it('shows total labeled images ', async () => {
        const unlabeledScreenshots = [mockedScreenshotThree];
        const labeledScreenshots = [mockedScreenshotOne, mockedScreenshotTwo];
        const screenshots = [...unlabeledScreenshots, ...labeledScreenshots];

        renderApp({
            labels: [mockedLabel],
            screenshots,
        });

        await waitFor(() => {
            expect(screen.getByRole('meter')).toHaveTextContent(`${mockedLabel.name}${labeledScreenshots.length}`);
        });
    });
});
