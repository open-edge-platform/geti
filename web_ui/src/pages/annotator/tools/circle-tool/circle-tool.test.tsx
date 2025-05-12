// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext, ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { CircleStateProvider } from './circle-state-provider.component';
import { CircleTool } from './circle-tool.component';
import { MIN_RADIUS } from './utils';

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const renderApp = async (annotationToolContext: AnnotationToolContext) => {
    jest.mocked(useAnnotationToolContext).mockReturnValue(annotationToolContext);

    const result = render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
            <TaskProvider>
                <CircleStateProvider>
                    <CircleTool annotationToolContext={annotationToolContext} />
                </CircleStateProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return result;
};

describe('CircleTool', (): void => {
    const defaultCircleSize = 10;

    const getToolSettings = jest.fn(() => ({ size: defaultCircleSize }));
    // @ts-expect-error We care only about mocking size
    const annotationToolContext = fakeAnnotationToolContext({ getToolSettings });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders a circle with default radius', async (): Promise<void> => {
        const { container } = await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: 40, clientY: 80 });
        const circle = container.querySelector('circle');

        expect(circle).toHaveAttribute('cx', '40');
        expect(circle).toHaveAttribute('cy', '80');
        expect(circle).toHaveAttribute('r', `${defaultCircleSize}`);
    });

    it('draws a circle of fixed size', async (): Promise<void> => {
        const onComplete = annotationToolContext.scene.addShapes;

        const { container } = await renderApp(annotationToolContext);
        expect(container.querySelector('circle')).toBeNull();

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 10, clientY: 20 });

        const circle = container.querySelector('circle');
        expect(circle).toHaveAttribute('cx', '10');
        expect(circle).toHaveAttribute('cy', '20');
        expect(circle).toHaveAttribute('r', `${defaultCircleSize}`);
        fireEvent.pointerUp(svg);

        expect(onComplete).toHaveBeenCalledWith([{ shapeType: ShapeType.Circle, x: 10, y: 20, r: defaultCircleSize }]);
    });

    it('draws a circle of fixed size even when moving the mouse a little bit', async (): Promise<void> => {
        const onComplete = annotationToolContext.scene.addShapes;

        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 10, clientY: 20 });
        fireEvent.pointerMove(svg, { buttons: 1, clientX: 10, clientY: 20 });
        fireEvent.pointerUp(svg, { buttons: 1, clientX: 10, clientY: 20 });

        expect(onComplete).toHaveBeenCalledWith([{ shapeType: ShapeType.Circle, x: 10, y: 20, r: defaultCircleSize }]);
    });

    it('draws a circle of larger size', async (): Promise<void> => {
        const onComplete = annotationToolContext.scene.addShapes;

        const { container } = await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerDown(svg, { buttons: 1, clientX: 40, clientY: 80 });

        const circle = container.querySelector('circle');
        expect(circle).toHaveAttribute('cx', '40');
        expect(circle).toHaveAttribute('cy', '80');

        // The radius is increased after moving the pointer
        expect(circle).toHaveAttribute('r', `${defaultCircleSize}`);
        fireEvent.pointerMove(svg, { clientX: 10, clientY: 80 });
        expect(circle).toHaveAttribute('r', '30');

        fireEvent.pointerUp(svg);

        expect(onComplete).toHaveBeenCalledWith([{ shapeType: ShapeType.Circle, x: 40, y: 80, r: 30 }]);
    });

    it('allows changing the default circle radius', async (): Promise<void> => {
        const onComplete = annotationToolContext.scene.addShapes;

        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { button: 2, buttons: 2, clientX: 10, clientY: 20 });
        fireEvent.pointerMove(svg, { clientX: 50, clientY: 20 });
        fireEvent.pointerUp(svg, { button: 2, buttons: 2, clientX: 50, clientY: 20 });

        expect(onComplete).toHaveBeenCalledWith([{ shapeType: ShapeType.Circle, x: 10, y: 20, r: 40 }]);
        expect(annotationToolContext.updateToolSettings).toHaveBeenCalledWith(ToolType.CircleTool, { size: 40 });
    });

    it('uses the default circle radius size when stamping', async (): Promise<void> => {
        const defaultRadius = 40;
        getToolSettings.mockReturnValueOnce({ size: defaultRadius });

        const { container } = await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: 50, clientY: 50 });

        const circle = container.querySelector('circle');
        expect(circle).toHaveAttribute('r', `${defaultRadius}`);
    });

    it('does not draw a smaller circle than MIN_RADIUS', async (): Promise<void> => {
        const { container } = await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 10, clientY: 10 });

        // Move outside the default radius to disable stamp mode
        fireEvent.pointerMove(svg, { clientX: 25, clientY: 25 });

        // Move back to the initial starting point
        fireEvent.pointerMove(svg, { clientX: 10, clientY: 10 });

        const circle = container.querySelector('circle');
        expect(circle).toHaveAttribute('r', `${MIN_RADIUS}`);
    });

    it('allows pressing esc to reset the tool', async () => {
        const onComplete = annotationToolContext.scene.addShapes;

        const { container } = await renderApp(annotationToolContext);
        expect(container.querySelector('circle')).toBeNull();

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { button: 2, buttons: 2, clientX: 10, clientY: 20 });
        fireEvent.pointerMove(svg, { clientX: 50, clientY: 20 });

        // Cancel the circle
        fireEvent.keyDown(svg, { key: 'Escape', code: 'Escape', charCode: 27 });

        // Completing the circle should have been cancelled
        fireEvent.pointerUp(svg, { button: 2, buttons: 2, clientX: 50, clientY: 20 });
        expect(onComplete).not.toHaveBeenCalled();
    });

    it('allows pressing esc to reset the tool after moving the cursor', async () => {
        const onComplete = annotationToolContext.scene.addShapes;

        const { container } = await renderApp(annotationToolContext);
        expect(container.querySelector('circle')).toBeNull();

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { button: 2, buttons: 2, clientX: 10, clientY: 20 });
        fireEvent.pointerMove(svg, { clientX: 50, clientY: 20 });

        // Cancel the circle
        fireEvent.keyDown(svg, { key: 'Escape', code: 'Escape', charCode: 27 });
        fireEvent.pointerMove(svg, { clientX: 10, clientY: 10 });

        // Completing the circle should have been cancelled
        fireEvent.pointerUp(svg, { button: 2, buttons: 2, clientX: 50, clientY: 20 });
        expect(onComplete).not.toHaveBeenCalled();
    });

    it('add circles partially drawn inside the roi', async () => {
        const onComplete = annotationToolContext.scene.addShapes;
        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');
        fireEvent.pointerDown(svg, { button: 2, buttons: 2, clientX: 1, clientY: 1 });
        fireEvent.pointerMove(svg, { clientX: 10, clientY: 0 });
        fireEvent.pointerUp(svg, { button: 2, buttons: 2, clientX: 10, clientY: 0 });
        expect(onComplete).toHaveBeenCalled();
    });

    it('does not add circles drawn outside the roi', async () => {
        const onComplete = annotationToolContext.scene.addShapes;
        await renderApp(annotationToolContext);

        const svg = screen.getByRole('editor');

        fireEvent.pointerDown(svg, { button: 2, buttons: 2, clientX: -50, clientY: -50 });
        fireEvent.pointerMove(svg, { clientX: -30, clientY: -50 });
        fireEvent.pointerUp(svg, { button: 2, buttons: 2, clientX: -30, clientY: -50 });

        expect(onComplete).not.toHaveBeenCalled();
    });
});
