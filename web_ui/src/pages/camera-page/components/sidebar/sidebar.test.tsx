// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { Label } from '../../../../core/labels/label.interface';
import {
    getMockedDatasetIdentifier,
    getMockedProjectIdentifier,
} from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { DeviceSettingsProvider } from '../../providers/device-settings-provider.component';
import { Sidebar } from './sidebar.component';

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

describe('Sidebar', () => {
    const mockedLabel = getMockedLabel();

    const renderApp = ({ labels = [] }: { labels: Label[] }) => {
        jest.mocked(useCameraParams).mockReturnValue({
            defaultLabelId: '',
            hasDefaultLabel: false,
            isLivePrediction: false,
            isPhotoCaptureMode: true,
            ...getMockedDatasetIdentifier(),
        });

        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                <DeviceSettingsProvider>
                    <Sidebar labels={labels} />
                </DeviceSettingsProvider>
            </ProjectProvider>
        );
    };

    it('toggle sidebar', async () => {
        const getOpenSidebarLabelMeter = () => screen.queryByRole('meter');

        renderApp({ labels: [mockedLabel] });

        await waitFor(() => {
            expect(getOpenSidebarLabelMeter()).toBeInTheDocument();
        });

        await userEvent.click(screen.getByRole('button', { name: 'toggle sidebar' }));

        expect(getOpenSidebarLabelMeter()).not.toBeInTheDocument();
    });
});
