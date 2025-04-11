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

import { fireEvent, screen } from '@testing-library/react';

import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import { PolygonStateContextProps, PolygonStateProvider, usePolygonState } from './polygon-state-provider.component';
import { PolygonMode } from './polygon-tool.enum';
import { SecondaryToolbar } from './secondary-toolbar.component';

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('./polygon-state-provider.component', () => {
    const actual = jest.requireActual('./polygon-state-provider.component');

    return {
        ...actual,
        usePolygonState: jest.fn(() => ({
            ...actual.usePolygonState(),
        })),
    };
});

const getToolSettings = jest.fn(() => ({ mode: null }));

// @ts-expect-error We only care about mocking polygon settings
const annotationToolContext = fakeAnnotationToolContext({ getToolSettings });

const renderToolbar = async () => {
    jest.mocked(useAnnotationToolContext).mockReturnValue(annotationToolContext);

    const { container } = await annotatorRender(
        <PolygonStateProvider>
            <SecondaryToolbar annotationToolContext={annotationToolContext} />
        </PolygonStateProvider>
    );

    return container;
};

const updateUsePolygonState = (data: Partial<PolygonStateContextProps>) => {
    jest.mocked(usePolygonState).mockImplementation(() => {
        const actual = jest.requireActual('./polygon-state-provider.component');
        const defaultOptions = { mode: PolygonMode.Polygon, setMode: jest.fn(), isIntelligentScissorsLoaded: false };

        return {
            ...actual,
            ...defaultOptions,
            ...data,
        };
    });
};

describe('Polygon tool SecondaryToolbar', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        jest.clearAllMocks();
    });

    describe('openCV module is not loaded', () => {
        it('Snapping is disabled', async () => {
            await renderToolbar();

            expect(screen.getByRole('switch')).toHaveAttribute('disabled');
        });

        it('Snapping is disabled when openCV module is not loaded', async () => {
            const mockSetMode = jest.fn();

            updateUsePolygonState({ setMode: mockSetMode });

            await renderToolbar();

            fireEvent.keyDown(document.body, { key: 'S', keyCode: 83, shiftKey: true });

            expect(screen.getByRole('switch')).toHaveAttribute('disabled');
            expect(mockSetMode).not.toHaveBeenCalled();
        });
    });

    describe('openCV module is loaded', () => {
        it('Snapping is enable', async () => {
            updateUsePolygonState({ isIntelligentScissorsLoaded: true });

            await renderToolbar();

            expect(screen.getByRole('switch')).not.toHaveAttribute('disabled');
        });

        it('change mode with Snapping hotkey', async () => {
            const mockSetMode = jest.fn();

            updateUsePolygonState({ setMode: mockSetMode, isIntelligentScissorsLoaded: true });

            await renderToolbar();

            fireEvent.keyDown(document.body, { key: 'S', keyCode: 83, shiftKey: true });

            expect(screen.getByRole('switch')).not.toHaveAttribute('disabled');
            expect(mockSetMode).toHaveBeenCalledWith(PolygonMode.MagneticLasso.toString());
        });
    });
});
