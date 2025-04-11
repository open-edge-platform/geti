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

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../project-details/providers/project-provider/project-provider.component';
import { CaptureMode, useCameraParams } from './camera-params.hook';

const wrapper = ({ children }: { children?: ReactNode }) => {
    return <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>{children}</ProjectProvider>;
};

const renderCameraParamsHook = ({
    initialEntries = [''],
    videoFlag = true,
}: {
    initialEntries: string[];
    videoFlag?: boolean;
}) => {
    return renderHookWithProviders(() => useCameraParams(), {
        wrapper,
        providerProps: {
            initialEntries,
            featureFlags: { FEATURE_FLAG_CAMERA_VIDEO_UPLOAD: videoFlag },
        },
    });
};

describe('useCameraParams', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('live prediction', () => {
        it('true', async () => {
            const { result } = renderCameraParamsHook({ initialEntries: ['?isLivePrediction=true'] });

            await waitFor(() => {
                expect(result.current.isLivePrediction).toBe(true);
            });
        });

        it('false', async () => {
            const { result } = renderCameraParamsHook({ initialEntries: ['?isLivePrediction=false'] });

            await waitFor(() => {
                expect(result.current.isLivePrediction).toBe(false);
            });
        });
    });

    it('hasDefaultLabel', async () => {
        const defaultLabelId = '123';
        const { result } = renderCameraParamsHook({ initialEntries: [`?defaultLabelId=${defaultLabelId}`] });

        await waitFor(() => {
            expect(result.current.hasDefaultLabel).toBe(true);
            expect(result.current.defaultLabelId).toBe(defaultLabelId);
        });
    });

    describe('isPhotoCaptureMode', () => {
        it('photo', async () => {
            const { result } = renderCameraParamsHook({ initialEntries: [`?captureMode=${CaptureMode.PHOTO}`] });

            await waitFor(() => {
                expect(result.current.isPhotoCaptureMode).toBe(true);
            });
        });

        it('video', async () => {
            const { result } = renderCameraParamsHook({ initialEntries: [`?captureMode=${CaptureMode.VIDEO}`] });

            await waitFor(() => {
                expect(result.current.isPhotoCaptureMode).toBe(false);
            });
        });
    });

    it('undefined params', async () => {
        const { result } = renderCameraParamsHook({ initialEntries: [''] });

        await waitFor(() => {
            expect(result.current.isLivePrediction).toBe(false);
        });

        expect(result.current.hasDefaultLabel).toBe(false);
        expect(result.current.defaultLabelId).toBe(null);
        expect(result.current.isPhotoCaptureMode).toBe(true);
    });
});
