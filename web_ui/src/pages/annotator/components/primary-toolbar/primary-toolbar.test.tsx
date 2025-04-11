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

import { fireEvent, screen, within } from '@testing-library/react';
import difference from 'lodash/difference';
import { TransformComponent } from 'react-zoom-pan-pinch';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { DETECTION_DOMAINS, SEGMENTATION_DOMAINS } from '../../../../core/projects/domains';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import {
    getMockedProject,
    mockedProjectContextProps,
} from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext, ANNOTATOR_MODE, ToolLabel } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useActiveTool } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { TaskContextProps, useTask } from '../../providers/task-provider/task-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { PrimaryToolbar } from './primary-toolbar.component';

jest.mock('../../hooks/use-annotator-mode', () => ({
    useAnnotatorMode: jest.fn(),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ workspaceId: 'workspace-id', projectId: 'project-id', organizationId: 'organization-123' }),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        tasks: [],
        selectedTask: null,
    })),
}));

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => mockedProjectContextProps({})),
}));

jest.mock('../../providers/task-chain-provider/use-task-chain-output.hook', () => ({
    ...jest.requireActual('../../providers/task-chain-provider/use-task-chain-output.hook'),
    useTaskChainOutput: jest.fn((context) =>
        jest.requireActual('../../providers/task-chain-provider/use-task-chain-output.hook').useTaskChainOutput(context)
    ),
}));

describe('Primary toolbar', (): void => {
    const App = ({ annotationToolContext }: { annotationToolContext?: AnnotationToolContext }) => {
        const [activeTool, setActiveTool] = useActiveTool();
        const mockContext = fakeAnnotationToolContext({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
            toggleTool: setActiveTool,
            ...annotationToolContext,
            tool: activeTool,
        });

        return (
            <ZoomProvider>
                <PrimaryToolbar annotationToolContext={mockContext} />
                <TransformComponent>{''}</TransformComponent>
            </ZoomProvider>
        );
    };

    const render = async (
        annotationToolContext?: AnnotationToolContext,
        tasksHook: Partial<TaskContextProps> = {},
        mode = ANNOTATOR_MODE.ACTIVE_LEARNING
    ) => {
        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ activeDomains: [DOMAIN.SEGMENTATION], ...tasksHook })
        );

        jest.mocked(useAnnotatorMode).mockReturnValue({
            currentMode: mode,
            isActiveLearningMode: mode === ANNOTATOR_MODE.ACTIVE_LEARNING,
        });

        await annotatorRender(<App annotationToolContext={annotationToolContext} />);
    };

    it('selects the circle tool', async () => {
        await render();

        const circleButton = screen.getByRole('button', { name: /Circle/ });

        expect(circleButton).not.toHaveAttribute('aria-pressed', 'true');

        fireEvent.click(circleButton);
        expect(circleButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('prediction mode hide annotation tools', async () => {
        const mockContext = fakeAnnotationToolContext({
            activeDomains: [DOMAIN.SEGMENTATION],
        });

        await render(mockContext, {}, ANNOTATOR_MODE.PREDICTION);

        expect(screen.getAllByRole('button')).toHaveLength(4);
        expect(screen.getByRole('button', { name: /Documentation actions/i })).toBeVisible();
        expect(screen.getByRole('button', { name: /Show dialog with hotkeys/i })).toBeVisible();
        expect(screen.getByRole('button', { name: /Canvas adjustments/i })).toBeVisible();
        expect(screen.getByRole('button', { name: /Fit image to screen/i })).toBeVisible();
    });

    describe('supported tools by domain', () => {
        const tools = Object.keys(ToolLabel);
        const toolsAndSupportedDomains = [
            [DOMAIN.SEGMENTATION, [ToolLabel.BoxTool, ToolLabel.CircleTool, ToolLabel.PolygonTool]],
            [DOMAIN.SEGMENTATION_INSTANCE, [ToolLabel.BoxTool, ToolLabel.CircleTool, ToolLabel.PolygonTool]],

            [DOMAIN.DETECTION, [ToolLabel.BoxTool]],
            [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX, [ToolLabel.RotatedBoxTool]],

            [DOMAIN.CLASSIFICATION, []],

            [DOMAIN.ANOMALY_CLASSIFICATION, []],
            [DOMAIN.ANOMALY_DETECTION, []],
            [DOMAIN.ANOMALY_SEGMENTATION, []],
        ];

        test.each(toolsAndSupportedDomains)('renders correct tools for %o', async (domain, domainTools) => {
            const mockContext = fakeAnnotationToolContext({});

            await render(mockContext, { activeDomains: [domain as DOMAIN] });

            const nonSupportedTools = difference(tools, domainTools);

            (domainTools as ToolLabel[]).forEach((tool) => {
                expect(screen.getByRole('button', { name: tool })).toBeInTheDocument();
            });

            nonSupportedTools.forEach((tool) => {
                expect(screen.queryByRole('button', { name: tool })).not.toBeInTheDocument();
            });
        });
    });

    it('shows tools for a classification -> segmentation task chain', async () => {
        const mockContext = fakeAnnotationToolContext({
            activeDomains: [DOMAIN.CLASSIFICATION, DOMAIN.SEGMENTATION],
        });

        await render(mockContext);

        expect(screen.getByRole('button', { name: /^Bounding Box$/ })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Rotated Bounding Box$/ })).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Circle/ })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Polygon/ })).toBeInTheDocument();
    });

    it('shows tools for a detection -> segmentation task chain', async () => {
        const mockContext = fakeAnnotationToolContext({
            activeDomains: [DOMAIN.DETECTION, DOMAIN.SEGMENTATION],
        });

        await render(mockContext);

        expect(screen.getByRole('button', { name: /^Bounding Box$/ })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Rotated Bounding Box$/ })).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Circle/ })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Polygon/ })).toBeInTheDocument();
    });

    it('should disable tools if user is on the second task without any input from the first one', async () => {
        const mockTaskOne = getMockedTask({ id: 'task-1', domain: DOMAIN.DETECTION });
        const mockTaskTwo = getMockedTask({ id: 'task-2', domain: DOMAIN.SEGMENTATION });

        const mockContext = fakeAnnotationToolContext({});

        await render(mockContext, {
            activeDomains: [DOMAIN.DETECTION, DOMAIN.SEGMENTATION],
            tasks: [mockTaskOne, mockTaskTwo],
            selectedTask: mockTaskTwo,
        });

        const baseDrawingToolsButtons = within(screen.getByTestId('base-drawing-tools-container')).getAllByRole(
            'button'
        );
        const smartDrawingToolsButtons = within(screen.getByTestId('smart-drawing-tools-container')).getAllByRole(
            'button'
        );
        const undoRedoButtons = within(screen.getByTestId('undo-redo-tools')).getAllByRole('button');

        baseDrawingToolsButtons.forEach((button) => expect(button).toBeDisabled());
        smartDrawingToolsButtons.forEach((button) => expect(button).toBeDisabled());
        undoRedoButtons.forEach((button) => expect(button).toBeDisabled());
    });

    describe('tools selected by default based on the project type', () => {
        it('Rotated bounding box tool should be selected by default in detection oriented project', async () => {
            const mockedTask = getMockedTask({ id: 'task-1', domain: DOMAIN.DETECTION_ROTATED_BOUNDING_BOX });
            const mockedContext = fakeAnnotationToolContext({});

            jest.mocked(useProject).mockImplementation(() =>
                mockedProjectContextProps({ project: getMockedProject({ tasks: [mockedTask] }) })
            );

            await render(mockedContext, {
                activeDomains: [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX],
                tasks: [mockedTask],
            });

            expect(screen.getByRole('button', { name: /Rotated Bounding Box$/ })).toHaveAttribute(
                'aria-pressed',
                'true'
            );
        });

        it.each(SEGMENTATION_DOMAINS)(
            'Polygon tool should be selected by default for segmentation projects',
            async (domain) => {
                const mockedTask = getMockedTask({ id: 'task-1', domain });
                const mockedContext = fakeAnnotationToolContext({});

                jest.mocked(useProject).mockImplementation(() =>
                    mockedProjectContextProps({ project: getMockedProject({ tasks: [mockedTask] }) })
                );

                await render(mockedContext, { activeDomains: [domain], tasks: [mockedTask] });

                expect(screen.getByRole('button', { name: /Polygon$/ })).toHaveAttribute('aria-pressed', 'true');
            }
        );

        it.each(DETECTION_DOMAINS)(
            'Bounding box tool is selected by default for detection projects',
            async (domain) => {
                const mockedTask = getMockedTask({ id: 'task-1', domain });
                const mockedContext = fakeAnnotationToolContext({});

                jest.mocked(useProject).mockImplementation(() =>
                    mockedProjectContextProps({ project: getMockedProject({ tasks: [mockedTask] }) })
                );

                await render(mockedContext, {
                    tasks: [getMockedTask({ id: 'task-1', domain })],
                    activeDomains: [domain],
                });

                expect(screen.getByRole('button', { name: /^Bounding Box$/ })).toHaveAttribute('aria-pressed', 'true');
            }
        );
    });
});
