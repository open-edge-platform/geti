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

import { Polygon } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { AnnotationToolContext, ToolType } from '../../core/annotation-tool-context.interface';
import { annotatorRender } from '../../test-utils/annotator-render';
import { RITMStateContextProps, useRITMState } from './ritm-state-provider.component';
import { defaultRITMConfig } from './ritm-tool.interface';
import { SecondaryToolbar } from './secondary-toolbar.component';

const mockRITM = () => {
    const mockedRITMState: RITMStateContextProps = {
        result: null,
        isLoading: false,
        loadImage: jest.fn(),
        execute: jest.fn(),
        cancel: jest.fn(),
        box: null,
        setBox: jest.fn(),
        isProcessing: false,
        reset: jest.fn(),
    };
    jest.mocked(useRITMState).mockImplementation(() => mockedRITMState);
    return mockedRITMState;
};

jest.mock('./ritm-state-provider.component.tsx', () => {
    return {
        useRITMState: jest.fn(),
    };
});

const mockLabels = [
    getMockedLabel({ id: '1', name: 'label-1' }),
    getMockedLabel({ id: '2', name: 'label-2' }),
    getMockedLabel({ id: '3', name: 'label-3' }),
];

const renderTool = async (rightConfig = defaultRITMConfig): Promise<AnnotationToolContext> => {
    const roi = { x: 0, y: 0, width: 1000, height: 1000 };
    const mockAnnotationToolContext = fakeAnnotationToolContext({
        tool: ToolType.RITMTool,
        labels: mockLabels,
        zoom: 1,
        roi,
    });

    // @ts-expect-error We only care about mocking ritm config
    mockAnnotationToolContext.getToolSettings = jest.fn(() => rightConfig);

    await annotatorRender(<SecondaryToolbar annotationToolContext={mockAnnotationToolContext} />);

    return mockAnnotationToolContext;
};

describe('RITM Secondary toolbar', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('dynamic selection mode', () => {
        it('toggle dynamic selection mode', async (): Promise<void> => {
            mockRITM();
            const annotationContext = await renderTool();

            fireEvent.click(screen.getByLabelText('Dynamic selection mode'));
            expect(annotationContext.updateToolSettings).toBeCalledWith(ToolType.RITMTool, {
                dynamicBoxMode: false,
                rightClickMode: false,
            });
        });
    });

    describe('Accept', () => {
        const getAcceptButton = () => screen.getByLabelText('accept ritm annotation');

        it('saves RITM found shapes to annotation scene', async (): Promise<void> => {
            const mockRITMState = mockRITM();
            const expectedContour: Polygon = { points: [{ x: 10, y: 10 }], shapeType: ShapeType.Polygon };
            mockRITMState.result = {
                shape: expectedContour,
                points: [{ x: 50, y: 50, positive: true }],
            };

            const annotationContext = await renderTool();

            fireEvent.click(getAcceptButton());
            expect(annotationContext.scene.addShapes).toBeCalledWith([expectedContour], undefined);
        });

        it('cannot save when RITM is still in progress', async (): Promise<void> => {
            const mockRITMState = mockRITM();
            const expectedContour: Polygon = { points: [{ x: 10, y: 10 }], shapeType: ShapeType.Polygon };
            mockRITMState.result = {
                shape: expectedContour,
                points: [{ x: 50, y: 50, positive: true }],
            };
            mockRITMState.isProcessing = true;

            const annotationContext = await renderTool();

            fireEvent.click(getAcceptButton());
            expect(annotationContext.scene.addShapes).not.toBeCalled();
        });

        it('right click mode stays active when was activated before accepting the results', async () => {
            const mockRITMState = mockRITM();
            const expectedContour: Polygon = { points: [{ x: 10, y: 10 }], shapeType: ShapeType.Polygon };
            mockRITMState.result = {
                shape: expectedContour,
                points: [{ x: 50, y: 50, positive: true }],
            };

            const annotationToolContext = await renderTool({ dynamicBoxMode: true, rightClickMode: true });

            expect(screen.getByRole('switch', { name: /right-click mode/i })).toBeEnabled();

            fireEvent.click(getAcceptButton());

            expect(annotationToolContext.updateToolSettings).not.toHaveBeenCalled();

            expect(screen.getByRole('switch', { name: /right-click mode/i })).toBeEnabled();
        });
    });

    describe('cancel', () => {
        it('resets asks RITM to reset', async (): Promise<void> => {
            const mockRITMState = mockRITM();
            const expectedContour: Polygon = { points: [{ x: 10, y: 10 }], shapeType: ShapeType.Polygon };
            mockRITMState.result = {
                shape: expectedContour,
                points: [{ x: 50, y: 50, positive: true }],
            };

            await renderTool();

            fireEvent.click(screen.getByLabelText('reject ritm annotation'));
            expect(mockRITMState.reset).toBeCalled();
        });
    });
});
