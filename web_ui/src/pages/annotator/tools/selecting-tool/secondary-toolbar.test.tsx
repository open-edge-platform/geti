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

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { CustomFeatureFlags } from '../../../../core/feature-flags/services/feature-flag-service.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { checkTooltip, getById, getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useVisibleAnnotations } from '../../hooks/use-visible-annotations.hook';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { TaskContextProps, useTask } from '../../providers/task-provider/task-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SelectingStateProvider } from './selecting-state-provider.component';
import { SelectingToolLabel, SelectingToolType } from './selecting-tool.enums';
import { getBrushMaxSize } from './utils';

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../hooks/use-visible-annotations.hook', () => ({
    useVisibleAnnotations: jest.fn(() => []),
}));

jest.mock('./selecting-state-provider.component', () => {
    const actual = jest.requireActual('./selecting-state-provider.component');
    return {
        ...actual,
        useSelectingState: jest.fn(() => actual.useSelectingState()),
    };
});

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        tasks: [],
        activeDomains: [],
        selectedTask: null,
        defaultLabel: null,
        isTaskChainDomainSelected: () => false,
    })),
}));

const renderToolbar = async ({
    annotations = [],
    tool = SelectingToolType.SelectionTool,
    tasksHook = {},
    featureFlags = {},
}: {
    annotations?: Annotation[];
    tasksHook?: Partial<TaskContextProps>;
    featureFlags?: CustomFeatureFlags;
    tool?: SelectingToolType;
}) => {
    const getToolSettings = jest.fn(() => ({ tool, stampedAnnotation: null }));

    // @ts-expect-error We only care about mocking selection settings
    const annotationToolContext = fakeAnnotationToolContext({ annotations, getToolSettings });

    jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ ...tasksHook }));

    jest.mocked(useAnnotationToolContext).mockReturnValue(annotationToolContext);

    const { container } = await annotatorRender(
        <SelectingStateProvider>
            <SecondaryToolbar annotationToolContext={annotationToolContext} />
        </SelectingStateProvider>,
        { featureFlags }
    );

    return { annotationToolContext, container };
};

describe('Selector Toolbar', () => {
    const DOMAINS_WITHOUT_SELECTION_TOOL_BUTTON = [
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.ANOMALY_DETECTION,
        DOMAIN.CLASSIFICATION,
        DOMAIN.ANOMALY_CLASSIFICATION,
    ];

    const DOMAINS_WITH_SELECTION_TOOL_BUTTON = [
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_SEGMENTATION,
    ];

    it('has title "Selector"', async () => {
        await renderToolbar({});

        expect(screen.getByText('Selector')).toBeInTheDocument();
    });

    it('has SelectionTool selected by default in segmentation projects', async () => {
        const tasks = [getMockedTask({ labels: [], domain: DOMAIN.SEGMENTATION })];
        const { container } = await renderToolbar({ tasksHook: { tasks, selectedTask: tasks[0] } });

        const selectionTool = getById(container, SelectingToolType.SelectionTool);

        expect(selectionTool).toBeInTheDocument();
        expect(selectionTool).toHaveAttribute('aria-pressed', 'true');
    });

    it.each(DOMAINS_WITH_SELECTION_TOOL_BUTTON)('selection tool is visible in %p', async (domain) => {
        const tasks = [getMockedTask({ labels: [], domain })];
        const { container } = await renderToolbar({ tasksHook: { tasks, selectedTask: tasks[0] } });

        const selectionTool = getById(container, SelectingToolType.SelectionTool);

        expect(selectionTool).toBeInTheDocument();
    });

    it.each(DOMAINS_WITHOUT_SELECTION_TOOL_BUTTON)('selection tool is not visible in %p', async (domain) => {
        const tasks = [getMockedTask({ labels: [], domain })];
        const { container } = await renderToolbar({ tasksHook: { tasks, selectedTask: tasks[0] } });

        const selectionTool = getById(container, SelectingToolType.SelectionTool);

        expect(selectionTool).not.toBeInTheDocument();
    });

    it('Classification project do not have subtools', async () => {
        const tasks = [getMockedTask({ id: '123', title: 'test', labels: [], domain: DOMAIN.CLASSIFICATION })];
        const { container } = await renderToolbar({ tasksHook: { tasks, selectedTask: tasks[0] } });

        const selectionTool = getById(container, SelectingToolType.SelectionTool);
        expect(selectionTool).not.toBeInTheDocument();
        expect(screen.queryByLabelText(SelectingToolLabel.BrushTool)).not.toBeInTheDocument();
    });

    describe('Brush tool', () => {
        const polygonAnnotation = getMockedAnnotation({ isSelected: true }, ShapeType.Polygon);

        it('render brush tool when one polygon shape annotation is selected', async () => {
            const tasks = [getMockedTask({ labels: [], domain: DOMAIN.SEGMENTATION })];
            const { annotationToolContext } = await renderToolbar({
                annotations: [polygonAnnotation],
                tasksHook: { tasks, selectedTask: tasks[0] },
            });

            const button = screen.getByLabelText(SelectingToolLabel.BrushTool);
            fireEvent.click(button);

            expect(annotationToolContext.updateToolSettings).toHaveBeenCalledWith(
                ToolType.SelectTool,
                expect.objectContaining({
                    tool: SelectingToolType.BrushTool,
                })
            );
        });

        it('render brush tool when one polygon shape annotation is selected in task chain', async () => {
            const tasks = [
                getMockedTask({ id: 'detection', labels: [], domain: DOMAIN.DETECTION }),
                getMockedTask({ id: 'segmentation', labels: [], domain: DOMAIN.SEGMENTATION }),
            ];

            const { annotationToolContext } = await renderToolbar({
                annotations: [polygonAnnotation],
                tasksHook: { tasks, selectedTask: null },
            });

            const button = screen.getByLabelText(SelectingToolLabel.BrushTool);
            fireEvent.click(button);

            expect(annotationToolContext.updateToolSettings).toHaveBeenCalledWith(
                ToolType.SelectTool,
                expect.objectContaining({
                    tool: SelectingToolType.BrushTool,
                })
            );
        });

        it('Brush tool is visible but disabled when multiple annotations are selected', async () => {
            const tasks = [getMockedTask({ labels: [], domain: DOMAIN.SEGMENTATION })];
            await renderToolbar({
                annotations: [polygonAnnotation, polygonAnnotation],
                tasksHook: {
                    tasks,
                    selectedTask: tasks[0],
                },
            });

            const button = screen.getByRole('button', { name: SelectingToolLabel.BrushTool });
            expect(button).toBeDisabled();

            await checkTooltip(button, 'Brush tool is disabled for multi-selection mode');
        });

        it('use RegionOfInterest to calc "maxBrushSize"', async () => {
            const tasks = [getMockedTask({ labels: [], domain: DOMAIN.SEGMENTATION })];
            await renderToolbar({
                annotations: [polygonAnnotation],
                tasksHook: {
                    tasks,
                    selectedTask: tasks[0],
                },
                tool: SelectingToolType.BrushTool,
            });

            const slider = screen.getByLabelText('brush-size');
            const input = slider.querySelector('input') as HTMLInputElement;

            expect(input.max).toBe(`${getBrushMaxSize(mockROI)}`);
        });
    });

    describe('Stamp tool', () => {
        const tasks = [getMockedTask({ labels: [], domain: DOMAIN.SEGMENTATION })];

        it('stamp tool should be hidden when there are no annotations selected', async () => {
            jest.mocked(useVisibleAnnotations).mockReturnValue([]);

            await renderToolbar({ tasksHook: { tasks, selectedTask: tasks[0] } });

            expect(screen.queryByRole('button', { name: 'Create stamp' })).not.toBeInTheDocument();
        });

        it('stamp tool should be hidden in classification task', async () => {
            const annotations = [getMockedAnnotation({ isSelected: true })];
            const classificationTask = [getMockedTask({ labels: [], domain: DOMAIN.CLASSIFICATION })];

            jest.mocked(useVisibleAnnotations).mockReturnValue(annotations);

            await renderToolbar({
                annotations,
                tasksHook: { tasks: classificationTask, selectedTask: classificationTask[0] },
            });

            expect(screen.queryByRole('button', { name: 'Create stamp' })).not.toBeInTheDocument();
        });

        it('stamp tool should be hidden in keypoint-detection task', async () => {
            const annotations = [getMockedAnnotation({ isSelected: true })];
            const keypointDetectionTask = getMockedTask({ labels: [], domain: DOMAIN.KEYPOINT_DETECTION });

            jest.mocked(useVisibleAnnotations).mockReturnValue(annotations);

            await renderToolbar({
                annotations,
                tasksHook: { tasks: [keypointDetectionTask], selectedTask: keypointDetectionTask },
            });

            expect(screen.queryByRole('button', { name: 'Create stamp' })).not.toBeInTheDocument();
        });

        it('stamp tool should be visible and active when there is selected annotation', async () => {
            const annotations = [getMockedAnnotation({ isSelected: true })];

            jest.mocked(useVisibleAnnotations).mockReturnValue(annotations);

            await renderToolbar({ annotations, tasksHook: { tasks, selectedTask: tasks[0] } });

            expect(screen.getByRole('button', { name: 'Create stamp' })).toBeInTheDocument();
            expect(screen.getByTestId('create-stamp-icon-id')).toBeInTheDocument();
        });

        it('stamp tool should be visible and inactive (disabled) when there are more than one selected annotation', async () => {
            const annotations = [
                getMockedAnnotation({ isSelected: true, id: 'ann-1' }),
                getMockedAnnotation({ isSelected: true, id: 'ann-2' }),
            ];

            jest.mocked(useVisibleAnnotations).mockReturnValue(annotations);

            await renderToolbar({ annotations, tasksHook: { tasks, selectedTask: tasks[0] } });

            const stampButton = screen.getByRole('button', { name: 'Create stamp' });

            expect(stampButton).toBeInTheDocument();
            expect(stampButton).toBeDisabled();

            await checkTooltip(
                screen.getByTestId('create-stamp-button-id'),
                'Stamp tool is disabled for multi-selection mode'
            );
        });
    });
});
