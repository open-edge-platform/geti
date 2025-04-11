// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { Rect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SSIMStateContextProps, SSIMStateProvider, useSSIMState } from './ssim-state-provider.component';

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('./ssim-state-provider.component', () => {
    const actual = jest.requireActual('./ssim-state-provider.component');
    return {
        ...actual,
        useSSIMState: jest.fn(() => ({
            ...actual.useSSIMState(),
        })),
    };
});

jest.mock('../../hooks/use-add-unfinished-shape.hook');

const updateSSIMStateImplementation = (data: Partial<SSIMStateContextProps>) => {
    jest.mocked(useSSIMState).mockImplementation(() => {
        const actual = jest.requireActual('./ssim-state-provider.component');

        return {
            ...actual,
            ...data,
        };
    });
};

const renderSecondaryToolbar = async () => {
    const getToolSettings = jest.fn(() => ({
        shapeType: ShapeType.Rect,
        autoMergeDuplicates: true,
    }));

    const mockAnnotationToolContext = fakeAnnotationToolContext({
        // @ts-expect-error We only care about mocking ssim settings
        getToolSettings,
        labels: [getMockedLabel({ name: 'label-1' }), getMockedLabel({ name: 'label-2' })],
    });

    jest.mocked(useAnnotationToolContext).mockReturnValue(mockAnnotationToolContext);

    render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <AnnotationSceneProvider annotations={[]} labels={[]}>
                    <SSIMStateProvider>
                        <SecondaryToolbar annotationToolContext={mockAnnotationToolContext} />
                    </SSIMStateProvider>
                </AnnotationSceneProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return mockAnnotationToolContext;
};

describe('SecondaryToolbar', () => {
    const getAcceptButton = () => screen.getByRole('button', { name: 'accept ssim annotation' });
    const getRejectButton = () => screen.getByRole('button', { name: 'reject ssim annotation' });

    it('clicking accept calls addShapes and reset', async () => {
        const shape: Rect = { shapeType: ShapeType.Rect, x: 0, y: 0, width: 30, height: 50 };
        const reset = jest.fn();

        updateSSIMStateImplementation({
            toolState: {
                shapes: [shape],
                matches: [{ shape, confidence: 1 }],
                threshold: 0,
            },
            reset,
        });

        const context = await renderSecondaryToolbar();

        const acceptButton = getAcceptButton();

        expect(acceptButton).toBeEnabled();

        fireEvent.click(acceptButton);

        expect(context.scene.addShapes).toBeCalledWith([shape], undefined);
        expect(reset).toBeCalled();
    });

    it('clicking reject resets the shapes', async () => {
        const shape: Rect = { shapeType: ShapeType.Rect, x: 0, y: 0, width: 30, height: 50 };
        const reset = jest.fn();

        updateSSIMStateImplementation({
            toolState: {
                shapes: [shape],
                matches: [{ shape, confidence: 1 }],
                threshold: 0,
            },
            reset,
        });

        const context = await renderSecondaryToolbar();
        const acceptButton = getAcceptButton();

        expect(acceptButton).toBeEnabled();

        fireEvent.click(getRejectButton());

        expect(context.scene.addShapes).toBeCalledTimes(0);
        expect(reset).toBeCalled();
    });

    describe('Detected items slider', () => {
        const getThresholdSlider = () => screen.queryByLabelText('Detection tool threshold slider button');

        it("is not visible when the tool hasn't been used yet", async () => {
            updateSSIMStateImplementation({
                toolState: {
                    shapes: [],
                    matches: [],
                    threshold: 0,
                },
            });

            await renderSecondaryToolbar();

            expect(getThresholdSlider()).not.toBeInTheDocument();
        });

        it('is disabled when there is only one match', async () => {
            const shape: Rect = { shapeType: ShapeType.Rect, x: 0, y: 0, width: 30, height: 50 };
            updateSSIMStateImplementation({
                toolState: {
                    shapes: [shape],
                    matches: [{ shape, confidence: 1 }],
                    threshold: 0,
                },
            });

            await renderSecondaryToolbar();

            expect(getThresholdSlider()).toBeDisabled();
        });

        it('is enabled when there are multiple matches', async () => {
            const shapes: Rect[] = [
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 30, height: 50 },
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 30, height: 50 },
            ];
            updateSSIMStateImplementation({
                toolState: {
                    shapes,
                    matches: shapes.map((shape) => ({ shape, confidence: 1 })),
                    threshold: 100,
                },
            });

            await renderSecondaryToolbar();

            expect(getThresholdSlider()).toBeEnabled();
        });
    });
});
