// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { TaskProvider, useTask } from '../../providers/task-provider/task-provider.component';
import { BoundingBoxTool } from './bounding-box-tool.component';

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({ defaultLabel: null, tasks: [], activeDomains: [] })),
}));

describe('BoundingBoxTool', () => {
    const renderApp = async (annotationToolContext: AnnotationToolContext) => {
        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                <TaskProvider>
                    <BoundingBoxTool annotationToolContext={annotationToolContext} />
                </TaskProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('draws a rectangle', async () => {
        const annotationToolContext = fakeAnnotationToolContext();
        const onComplete = annotationToolContext.scene.addShapes;
        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: 40, clientY: 80 });
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 40, clientY: 80 });

        const rect = screen.getByRole('application');
        expect(rect).toHaveAttribute('x', '40');
        expect(rect).toHaveAttribute('y', '80');
        expect(rect).toHaveAttribute('width', '0');
        expect(rect).toHaveAttribute('height', '0');

        fireEvent.pointerMove(svg, { clientX: 10, clientY: 30 });
        expect(rect).toHaveAttribute('x', '10');
        expect(rect).toHaveAttribute('y', '30');
        expect(rect).toHaveAttribute('width', '30');
        expect(rect).toHaveAttribute('height', '50');

        fireEvent.pointerUp(svg);

        expect(onComplete).toBeCalledWith([{ shapeType: ShapeType.Rect, x: 10, y: 30, width: 30, height: 50 }]);
    });

    it('creates rotated bounding boxs when in a rotated detection task', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});
        const onComplete = annotationToolContext.scene.addShapes;

        jest.mocked(useTask).mockReturnValueOnce(
            mockedTaskContextProps({ activeDomains: [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX] })
        );

        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: 40, clientY: 80 });
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 40, clientY: 80 });
        fireEvent.pointerMove(svg, { clientX: 10, clientY: 30 });
        fireEvent.pointerUp(svg);

        expect(onComplete).toBeCalledWith([
            { shapeType: ShapeType.RotatedRect, x: 25, y: 55, width: 30, height: 50, angle: 0 },
        ]);
    });

    it('allows pressing esc to reset the tool', async () => {
        const annotationToolContext = fakeAnnotationToolContext();
        const onComplete = annotationToolContext.scene.addShapes;

        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: 40, clientY: 80 });
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 40, clientY: 80 });
        fireEvent.pointerMove(svg, { clientX: 10, clientY: 30 });

        // Cancel the bounding box
        fireEvent.keyDown(svg, { key: 'Escape', code: 'Escape', charCode: 27 });

        // Completing the bounding box should have been cancelled
        fireEvent.pointerUp(svg);
        expect(onComplete).not.toBeCalled();
    });

    it('does not add bounding box outside the roi', () => {
        const roi = { x: 50, y: 50, width: 100, height: 100 };
        const annotationToolContext = fakeAnnotationToolContext();

        jest.mocked(useROI).mockReturnValueOnce({
            roi,
            image: mockImage,
        });

        const onComplete = annotationToolContext.scene.addShapes;

        render(<BoundingBoxTool annotationToolContext={annotationToolContext} />);

        const svg = screen.getByRole('editor');

        fireEvent.pointerDown(svg, { buttons: 1, clientX: 0, clientY: 0 });
        fireEvent.pointerMove(svg, { clientX: roi.x - 1, clientY: roi.y - 1 });
        fireEvent.pointerUp(svg);

        expect(onComplete).not.toBeCalled();
    });

    it('does not add partially inside bounding box', () => {
        const roi = { x: 50, y: 50, width: 100, height: 100 };
        const annotationToolContext = fakeAnnotationToolContext();

        jest.mocked(useROI).mockReturnValueOnce({
            roi,
            image: mockImage,
        });

        const onComplete = annotationToolContext.scene.addShapes;

        render(<BoundingBoxTool annotationToolContext={annotationToolContext} />);

        const svg = screen.getByRole('editor');

        fireEvent.pointerDown(svg, { buttons: 1, clientX: 0, clientY: 0 });
        fireEvent.pointerMove(svg, { clientX: roi.x + 1, clientY: roi.y + 1 });
        fireEvent.pointerUp(svg);

        expect(onComplete).not.toBeCalled();
    });
});
