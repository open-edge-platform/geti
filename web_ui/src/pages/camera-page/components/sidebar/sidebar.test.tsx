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
