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

import '@wessberg/pointer-events';

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { ToolSettings, ToolType } from '../../core/annotation-tool-context.interface';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationToolProvider } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotator } from '../../providers/annotator-provider/annotator-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SSIMStateProvider } from './ssim-state-provider.component';
import { SSIMTool } from './ssim-tool.component';
import { RunSSIMProps, SSIMMatch, SSIMMethods } from './ssim-tool.interface';
import { convertToRect } from './util';

jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(),
}));

jest.mock('../../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

const mockROI = getMockedROI({ x: 0, y: 0, width: 1000, height: 1000 });
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../hooks/use-add-unfinished-shape.hook');

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

jest.mock('../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook', () => {
    return {
        ...jest.requireActual('../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook'),
        useLoadAIWebworker: jest.fn(),
    };
});

const mockLabels = [
    getMockedLabel({ id: '1', name: 'label-1' }),
    getMockedLabel({ id: '2', name: 'label-2' }),
    getMockedLabel({ id: '3', name: 'label-3' }),
];

// NOTE: In the future, the way we mock webworkers will change, we will have a clearer
// separation between the workers and geti, and provide a MockWorker to be able to use with tests
const createFakeSSIM = (shapes: Shape[]) => {
    class FakeSSIM implements SSIMMethods {
        executeSSIM(_props: RunSSIMProps): SSIMMatch[] {
            return shapes.map((shape) => ({ shape: convertToRect(shape), confidence: 1 }));
        }
    }

    return {
        SSIM: FakeSSIM,
        terminate: () => {
            console.warn('Worker terminated');
        },
    };
};
const mockSSIMWorker = (shapes: Shape[]) => {
    const FakeSSIM = createFakeSSIM(shapes);

    jest.mocked(useLoadAIWebworker).mockImplementation(() => {
        return {
            worker: FakeSSIM,
        };
    });
};

const renderTool = async (toolSettings: Partial<ToolSettings[ToolType.SSIMTool]> = {}) => {
    const mockAnnotationToolContext = fakeAnnotationToolContext({
        tool: ToolType.SSIMTool,
        labels: mockLabels,
        zoom: 1,
    });

    mockAnnotationToolContext.getToolSettings = jest.fn().mockImplementation(() => ({
        autoMergeDuplicates: true,
        shapeType: ShapeType.Rect,
        threshold: 0,
        ...toolSettings,
    }));

    const selectedMediaItem = {
        ...getMockedImageMediaItem({}),
        image: mockImage,
        annotations: mockAnnotationToolContext.scene.annotations,
    };

    // @ts-expect-error We only care about mocking tool stuff
    jest.mocked(useAnnotator).mockReturnValue({
        activeTool: ToolType.SSIMTool,
        setActiveTool: jest.fn(),
    });

    // @ts-expect-error We only care about selectedMediaItem stuff
    jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem });

    providersRender(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <AnnotationSceneProvider annotations={[]} labels={[]}>
                    <AnnotationToolProvider>
                        <SSIMStateProvider>
                            <SSIMTool annotationToolContext={mockAnnotationToolContext} />
                            <SecondaryToolbar annotationToolContext={mockAnnotationToolContext} />
                        </SSIMStateProvider>
                    </AnnotationToolProvider>
                </AnnotationSceneProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return mockAnnotationToolContext;
};

describe('SSIMTool', () => {
    const getAcceptButton = () => screen.getByRole('button', { name: 'accept ssim annotation' });

    afterAll(() => {
        jest.clearAllMocks();
    });

    it('drawing a square fires the ssim worker and accepting it saves it to annotation', async () => {
        const shapes: Shape[] = [
            { shapeType: ShapeType.Rect, x: 10, y: 30, width: 30, height: 50 },
            { shapeType: ShapeType.Rect, x: 50, y: 60, width: 30, height: 50 },
        ];

        mockSSIMWorker(shapes);

        const annotationContext = await renderTool();
        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: 40, clientY: 80 });
        fireEvent.pointerDown(svg, { buttons: 1, clientX: 40, clientY: 80 });

        fireEvent.pointerMove(svg, { clientX: 10, clientY: 30 });
        const rect = screen.getByRole('application');
        expect(rect).toHaveAttribute('x', '10');
        expect(rect).toHaveAttribute('y', '30');
        expect(rect).toHaveAttribute('width', '30');
        expect(rect).toHaveAttribute('height', '50');

        fireEvent.pointerUp(svg);

        // Wait for ssim worker to complete, by checking if the confirm button is enabled
        await waitFor(() => {
            expect(getAcceptButton()).toBeEnabled();
        });

        // Make sure that all rectangles returned by the SSIM worker are drawn
        expect(screen.getAllByRole('application')).toHaveLength(shapes.length);

        fireEvent.click(getAcceptButton());

        expect(annotationContext.scene.addShapes).toHaveBeenCalledWith(shapes, undefined);
    });

    it('drawing when circle is selected draws circle', async () => {
        const from = { clientX: 40, clientY: 80 };
        const to = { clientX: 10, clientY: 30 };
        const r = Math.round(
            Math.sqrt(Math.pow(to.clientX - from.clientX, 2) + Math.pow(to.clientY - from.clientY, 2))
        );

        const shapes: Shape[] = [{ shapeType: ShapeType.Circle, x: from.clientX, y: from.clientY, r }];

        mockSSIMWorker(shapes);

        const annotationContext = await renderTool({ shapeType: ShapeType.Circle });

        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, from);
        fireEvent.pointerDown(svg, { buttons: 1, ...from });

        fireEvent.pointerMove(svg, to);
        const circle = screen.getByRole('application');
        expect(circle).toHaveAttribute('cx', '40');
        expect(circle).toHaveAttribute('cy', '80');
        expect(circle).toHaveAttribute('r', r.toString());

        fireEvent.pointerUp(svg);

        // Wait for ssim worker to complete, by checking if the confirm button is enabled
        await waitFor(() => {
            expect(getAcceptButton()).toBeEnabled();
        });

        // Make sure that the circle returned by the SSIM worker are drawn
        const circleSSIM = screen.getByRole('application');

        expect(circleSSIM).toHaveAttribute('cx', '40');
        expect(circleSSIM).toHaveAttribute('cy', '80');
        expect(circleSSIM).toHaveAttribute('r', r.toString());

        fireEvent.click(getAcceptButton());
        expect(annotationContext.scene.addShapes).toHaveBeenCalled();
    });
});
