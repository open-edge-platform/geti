// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { act, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Point } from '../../../../core/annotations/shapes.interface';
import { ProjectProps } from '../../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { KeypointStructure } from '../../../../core/projects/task.interface';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedKeypointTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { annotatorRender } from '../../../annotator/test-utils/annotator-render';
import { ProjectTemplate } from './project-template.component';

jest.mock('../../../../hooks/use-history-block/use-history-block.hook', () => ({
    useHistoryBlock: () => {
        return [false, jest.fn(), jest.fn()];
    },
}));

jest.mock('../../../../hooks/use-debounced-callback/use-debounced-callback.hook', () => ({
    useDebouncedCallback: jest.fn((callback) => callback),
}));

const point1Position = {
    current: { x: 100, y: 100 },
    currentNormalized: { x: 0.1, y: 0.1 }, //roi size 1000 X 1000
    new: { x: 600, y: 600 },
    newNormalized: { x: 0.6, y: 0.6 }, //roi size 1000 X 1000
};

const keypointStructure: KeypointStructure = {
    edges: [{ nodes: ['label 1', 'label 2'] }],
    positions: [
        getMockedKeypointNode({
            ...point1Position.currentNormalized,
            label: getMockedLabel({ id: 'label 1', name: 'label 1', color: '#fff' }),
        }),
        getMockedKeypointNode({
            x: 0.2,
            y: 0.2,
            label: getMockedLabel({ id: 'label 2', name: 'label 2', color: '#fff' }),
        }),
    ],
};

const movePoint = (element: HTMLElement, point: Point, newPoint: Point) => {
    act(() => {
        element.dispatchEvent(
            new MouseEvent('pointerdown', {
                bubbles: true,
                cancelable: true,
                clientX: point.x,
                clientY: point.y,
            })
        );
    });
    act(() => {
        element.dispatchEvent(
            new MouseEvent('pointermove', {
                bubbles: true,
                cancelable: true,
                clientX: newPoint.x,
                clientY: newPoint.y,
            })
        );
    });
    act(() => {
        element.dispatchEvent(new MouseEvent('pointerup', { bubbles: true, cancelable: true }));
    });
};

describe('ProjectTemplate', () => {
    const renderApp = async ({ mockedProject }: { mockedProject: ProjectProps }) => {
        const projectService = createInMemoryProjectService();
        projectService.editProject = jest.fn();
        projectService.getProject = async () => mockedProject;

        await annotatorRender(<ProjectTemplate />, { services: { projectService } });

        return { projectService };
    };

    beforeEach(() => {
        // TODO UI: Move to setupTests and ensure other tests (e.g., ritm-tool.test) continue to work without issues.
        SVGElement.prototype.setPointerCapture = jest.fn();
        SVGElement.prototype.releasePointerCapture = jest.fn();
    });

    it('hides template and hotkeys options', async () => {
        const mockedProject = getMockedProject({ tasks: [getMockedKeypointTask({ keypointStructure })] });
        await renderApp({ mockedProject });

        expect(screen.getByRole('button', { name: /update template/i })).toBeDisabled();
        expect(screen.queryByRole('button', { name: /templates menu/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /show dialog with hotkeys/i })).not.toBeInTheDocument();
    });

    it('submits the updated keypoint position', async () => {
        const [point1] = keypointStructure.positions;
        const mockedProject = getMockedProject({ tasks: [getMockedKeypointTask({ keypointStructure })] });

        const { projectService } = await renderApp({ mockedProject });

        expect(screen.getByRole('button', { name: 'Update Template' })).toBeDisabled();

        movePoint(
            screen.getByLabelText(`keypoint ${point1.label.name} anchor`),
            point1Position.current,
            point1Position.new
        );

        await userEvent.click(screen.getByRole('button', { name: 'Update Template' }));

        expect(projectService.editProject).toHaveBeenCalledWith(
            expect.anything(),
            expect.objectContaining({
                tasks: [
                    expect.objectContaining({
                        keypointStructure: {
                            edges: keypointStructure.edges,
                            positions: expect.arrayContaining([
                                { label: point1.label.name, ...point1Position.newNormalized },
                            ]),
                        },
                    }),
                ],
            }),
            true
        );
    });

    it('submits updated label name', async () => {
        const newLabelName = 'new test name';
        const [point1] = keypointStructure.positions;
        const mockedProject = getMockedProject({ tasks: [getMockedKeypointTask({ keypointStructure })] });

        const { projectService } = await renderApp({ mockedProject });

        expect(screen.getByRole('button', { name: 'Update Template' })).toBeDisabled();

        await userEvent.click(screen.getByLabelText(`keypoint ${point1.label.name} anchor`));
        await userEvent.clear(screen.getByRole('textbox', { name: 'label name input' }));
        await userEvent.type(screen.getByRole('textbox', { name: 'label name input' }), newLabelName);

        await userEvent.click(screen.getByRole('button', { name: 'Update Template' }));

        expect(projectService.editProject).toHaveBeenLastCalledWith(
            expect.anything(),
            expect.objectContaining({
                tasks: [
                    expect.objectContaining({
                        keypointStructure: {
                            edges: [{ nodes: [newLabelName, 'label 2'] }],
                            positions: expect.arrayContaining([{ label: newLabelName, x: point1.x, y: point1.y }]),
                        },
                        labels: expect.arrayContaining([
                            expect.objectContaining({ id: 'label 1', name: newLabelName }),
                        ]),
                    }),
                ],
            }),
            true
        );
    });
});
