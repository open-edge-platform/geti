// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { TaskChainInput } from '../../../../core/annotations/annotation.interface';
import { getBoundingBox } from '../../../../core/annotations/math';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { RequiredProviders } from '../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext, ToolSettings, ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider, useTask } from '../../providers/task-provider/task-provider.component';
import { RITMStateContextProps, useRITMState } from './ritm-state-provider.component';
import { RITMTool } from './ritm-tool.component';
import { defaultRITMConfig } from './ritm-tool.interface';

const mockRITM = () => {
    const mockedRITMState: RITMStateContextProps = {
        result: null,
        isLoading: false,
        cancel: jest.fn(),
        execute: jest.fn(),
        box: null,
        setBox: jest.fn(),
        isProcessing: false,
        reset: jest.fn(),
    };

    jest.mocked(useRITMState).mockImplementation(() => mockedRITMState);
    jest.mocked(useTaskChain).mockImplementation(() => ({ inputs: [], outputs: [] }));
    jest.mocked(useROI).mockReturnValue({ roi: mockROI, image: mockImage });

    return mockedRITMState;
};

const taskChainROI = { x: 100, y: 50, width: 100, height: 100 };

const mockRITMWithTaskChain = () => {
    const state = mockRITM();

    const inputs: TaskChainInput[] = [
        {
            id: 'task-chain-annotation',
            isSelected: true,
            isHidden: false,
            isLocked: false,
            labels: [],
            zIndex: 0,
            shape: { ...taskChainROI, shapeType: ShapeType.Rect },
            outputs: [],
        },
    ];
    jest.mocked(useTaskChain).mockImplementation(() => ({ inputs, outputs: [] }));
    jest.mocked(useROI).mockReturnValue({ roi: getBoundingBox(inputs[0].shape), image: mockImage });

    return state;
};

jest.mock('./ritm-state-provider.component.tsx', () => {
    return {
        useRITMState: jest.fn(),
    };
});

jest.mock('../../providers/task-chain-provider/task-chain-provider.component', () => {
    return {
        useTaskChain: jest.fn().mockImplementation(() => ({ inputs: [] })),
    };
});

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({ defaultLabel: null, tasks: [], activeDomains: [] })),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const mockROI = { x: 0, y: 0, width: 1000, height: 1000 };
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

const mockLabels = [
    getMockedLabel({ id: '1', name: 'label-1' }),
    getMockedLabel({ id: '2', name: 'label-2' }),
    getMockedLabel({ id: '3', name: 'label-3' }),
];

const renderTool = (toolSettings: Partial<ToolSettings[ToolType.RITMTool]> = {}): AnnotationToolContext => {
    const mockAnnotationToolContext = fakeAnnotationToolContext({
        tool: ToolType.RITMTool,
        labels: mockLabels,
        zoom: 1,
    });

    // @ts-expect-error We only care about mocking ritm config
    mockAnnotationToolContext.getToolSettings = jest.fn(() => ({ ...defaultRITMConfig, ...toolSettings }));

    render(
        <RequiredProviders>
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <TaskProvider>
                    <RITMTool annotationToolContext={mockAnnotationToolContext} />
                </TaskProvider>
            </ProjectProvider>
        </RequiredProviders>
    );

    return mockAnnotationToolContext;
};

describe('RITMTool', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('dynamic selection mode', () => {
        it('initial click uses area around click', async (): Promise<void> => {
            const mockedRITMState = mockRITM();

            renderTool();

            const editor = await screen.findByRole('editor');

            fireEvent.pointerMove(editor, { clientX: 50, clientY: 50 });
            fireEvent.mouseDown(editor, { buttons: 0, clientX: 50, clientY: 50 });
            fireEvent.mouseUp(editor, { buttons: 0, clientX: 50, clientY: 50 });

            await waitFor(() => {
                expect(mockedRITMState.execute).toHaveBeenCalledWith(
                    mockImage,
                    { x: 0, y: 0, width: 300, height: 300 },
                    [{ x: 50, y: 50, positive: true }],
                    ShapeType.Polygon
                );
            });
        });

        it('ignores clicks when ritm is processing', async (): Promise<void> => {
            const mockedRITMState = mockRITM();

            mockedRITMState.box = { x: 0, y: 0, width: 300, height: 200 };
            mockedRITMState.isProcessing = true;

            renderTool();

            const pointOne = { x: 50, y: 50, positive: true };
            const pointTwo = { clientX: 100, clientY: 100 };

            const searchRegion = { x: 0, y: 0, width: 300, height: 200 };
            const editor = await screen.findByRole('editor');

            mockedRITMState.box = searchRegion;
            mockedRITMState.result = {
                shape: { points: [], shapeType: ShapeType.Polygon },
                points: [pointOne],
            };

            fireEvent.pointerMove(editor, pointTwo);
            fireEvent.mouseDown(editor, { buttons: 0, ...pointTwo });
            fireEvent.mouseUp(editor, { buttons: 0, ...pointTwo });

            await waitFor(() => {
                expect(mockedRITMState.execute).not.toHaveBeenCalled();
            });
        });

        it('points used in RITM are drawn on image', async (): Promise<void> => {
            const mockedRITMState = mockRITM();

            const points = [
                { x: 50, y: 50, positive: true },
                { x: 10, y: 80, positive: true },
            ];

            mockedRITMState.box = { x: 0, y: 0, width: 300, height: 200 };
            mockedRITMState.result = {
                shape: { points: [], shapeType: ShapeType.Polygon },
                points,
            };

            renderTool();

            const editor = await screen.findByRole('editor');
            const circles = editor.querySelectorAll('circle');

            circles.forEach((circle, index) => {
                expect(circle.getAttribute('cx')).toBe(String(points[index].x));
                expect(circle.getAttribute('cy')).toBe(String(points[index].y));
            });
        });

        describe('taskChain', () => {
            it('adds point if clicking inside the ROI of the taskChain', async () => {
                const mockedRITMState = mockRITMWithTaskChain();

                renderTool();

                const editor = await screen.findByRole('editor');

                const point = { clientX: 150, clientY: 100 };

                fireEvent.pointerMove(editor, point);
                fireEvent.mouseDown(editor, { buttons: 0, ...point });
                fireEvent.mouseUp(editor, { buttons: 0, ...point });

                await waitFor(() => {
                    expect(mockedRITMState.execute).toHaveBeenCalledWith(
                        mockImage,
                        { x: 100, y: 50, width: 100, height: 100 },
                        [{ x: 150, y: 100, positive: true }],
                        ShapeType.Polygon
                    );
                });
            });

            it('box is limited to the ROI', async () => {
                const mockedRITMState = mockRITMWithTaskChain();

                renderTool();

                const editor = await screen.findByRole('editor');

                const point = { clientX: 150, clientY: 100 };

                fireEvent.pointerMove(editor, point);
                fireEvent.mouseDown(editor, { buttons: 0, ...point });
                fireEvent.mouseUp(editor, { buttons: 0, ...point });

                await waitFor(() => {
                    expect(mockedRITMState.execute).toHaveBeenCalledWith(
                        mockImage,
                        taskChainROI,
                        [{ x: 150, y: 100, positive: true }],
                        ShapeType.Polygon
                    );
                });
            });

            it('ignores clicks if clicking outside the ROI of the taskChain', async () => {
                const mockedRITMState = mockRITMWithTaskChain();

                renderTool();

                const editor = await screen.findByRole('editor');

                const point = { clientX: 300, clientY: 500 };

                fireEvent.pointerMove(editor, point);
                fireEvent.mouseDown(editor, { buttons: 0, ...point });
                fireEvent.mouseUp(editor, { buttons: 0, ...point });

                await waitFor(() => {
                    expect(mockedRITMState.execute).not.toHaveBeenCalled();
                });
            });
        });
    });

    describe('default mode', () => {
        const points = [{ x: 30, y: 50, positive: true }];
        const contourPoints = [
            { x: 0, y: 0 },
            { x: 100, y: 0 },
            { x: 100, y: 100 },
            { x: 0, y: 100 },
        ];

        it('should not add any points on right click when right click mode is disabled', async () => {
            const mockedRITMState = mockRITM();

            mockedRITMState.box = { x: 0, y: 0, width: 300, height: 200 };
            mockedRITMState.result = {
                shape: { points: contourPoints, shapeType: ShapeType.Polygon },
                points,
            };

            renderTool({ rightClickMode: false });
            const editor = await screen.findByRole('editor');

            const outside = { clientX: 110, clientY: 50 };
            fireEvent.pointerMove(editor, outside);
            fireEvent.mouseDown(editor, { buttons: 2, ...outside });
            fireEvent.mouseUp(editor, { buttons: 2, ...outside });

            await waitFor(() => {
                expect(mockedRITMState.execute).not.toHaveBeenCalled();
            });
        });

        it('should add points on right click when right click mode is enabled', async () => {
            const mockedRITMState = mockRITM();

            mockedRITMState.box = { x: 0, y: 0, width: 300, height: 200 };
            mockedRITMState.result = {
                shape: { points: contourPoints, shapeType: ShapeType.Polygon },
                points,
            };

            renderTool({ rightClickMode: true });
            const editor = await screen.findByRole('editor');

            const outside = { clientX: 110, clientY: 50 };
            fireEvent.pointerMove(editor, outside);
            fireEvent.mouseDown(editor, { buttons: 2, ...outside });
            fireEvent.mouseUp(editor, { buttons: 2, ...outside });

            await waitFor(() => {
                expect(mockedRITMState.execute).toHaveBeenCalled();
            });
        });

        it('creates positive point when clicking outside existing polygon', async () => {
            const mockedRITMState = mockRITM();

            mockedRITMState.result = {
                shape: { points: contourPoints, shapeType: ShapeType.Polygon },
                points,
            };

            renderTool({ rightClickMode: false });
            const editor = await screen.findByRole('editor');

            const outside = { clientX: 110, clientY: 50 };
            fireEvent.pointerMove(editor, outside);
            fireEvent.mouseDown(editor, { buttons: 0, ...outside });
            fireEvent.mouseUp(editor, { buttons: 0, ...outside });

            await waitFor(() => {
                expect(mockedRITMState.execute).toHaveBeenCalledWith(
                    mockImage,
                    { x: 0, y: 0, width: 360, height: 300 },
                    [
                        { x: 30, y: 50, positive: true },
                        { x: 110, y: 50, positive: true },
                    ],
                    ShapeType.Polygon
                );
            });
        });

        it('creates negative point when clicking inside existing polygon', async () => {
            const mockedRITMState = mockRITM();

            mockedRITMState.result = {
                shape: { points: contourPoints, shapeType: ShapeType.Polygon },
                points,
            };

            renderTool({ rightClickMode: false });
            const editor = await screen.findByRole('editor');

            const center = { clientX: 50, clientY: 50 };
            fireEvent.pointerMove(editor, center);
            fireEvent.mouseDown(editor, { buttons: 0, ...center });
            fireEvent.mouseUp(editor, { buttons: 0, ...center });

            await waitFor(() => {
                expect(mockedRITMState.execute).toHaveBeenCalledWith(
                    mockImage,
                    { x: 0, y: 0, width: 300, height: 300 },
                    [
                        { x: 30, y: 50, positive: true },
                        { x: 50, y: 50, positive: false },
                    ],
                    ShapeType.Polygon
                );
            });
        });

        it('should not use exiting bounding box for new entry point', async () => {
            const mockedRITMState = mockRITM();

            mockedRITMState.box = { x: 0, y: 0, width: 300, height: 200 };
            mockedRITMState.result = {
                shape: { points: contourPoints, shapeType: ShapeType.Polygon },
                points,
            };

            renderTool({ rightClickMode: false });
            const editor = await screen.findByRole('editor');

            const outside = { clientX: 110, clientY: 50 };

            fireEvent.pointerMove(editor, outside);
            fireEvent.mouseDown(editor, { buttons: 0, ...outside });
            fireEvent.mouseUp(editor, { buttons: 0, ...outside });

            await waitFor(() => {
                expect(mockedRITMState.execute).toHaveBeenCalledWith(
                    mockImage,
                    { x: 0, y: 0, width: 360, height: 300 },
                    [
                        { x: 30, y: 50, positive: true },
                        { x: 110, y: 50, positive: true },
                    ],
                    ShapeType.Polygon
                );
            });
        });
    });

    describe('draw box mode', () => {
        it('drawing box sets the box for RITM', async (): Promise<void> => {
            const mockedRITMState = mockRITM();

            renderTool({ dynamicBoxMode: false });

            const pointOne = { clientX: 100, clientY: 100 };
            const pointTwo = { clientX: 300, clientY: 200 };
            const expectedBox = { x: 100, y: 100, width: 200, height: 100 };

            const editor = await screen.findByRole('editor');

            fireEvent.pointerMove(editor, pointOne);
            fireEvent.pointerDown(editor, { buttons: 0, ...pointOne });
            fireEvent.pointerMove(editor, pointTwo);
            fireEvent.pointerUp(editor, { buttons: 0, ...pointTwo });

            await waitFor(() => {
                expect(mockedRITMState.setBox).toHaveBeenCalledWith(expectedBox);
            });
        });

        it('clicking outside box resets box', async (): Promise<void> => {
            const mockedRITMState = mockRITM();

            mockedRITMState.box = { x: 100, y: 100, width: 200, height: 100 };

            await renderTool({ dynamicBoxMode: false });

            const pointOne = { clientX: 50, clientY: 50 };

            const editor = await screen.findByRole('editor');

            fireEvent.pointerMove(editor, pointOne);
            fireEvent.mouseDown(editor, { buttons: 0, ...pointOne });
            fireEvent.mouseUp(editor, { buttons: 0, ...pointOne });

            expect(mockedRITMState.setBox).toHaveBeenCalledWith(null);
        });
    });

    describe('Additional outputs', () => {
        it('shows a rotated box when used in rotated bounding box project', async (): Promise<void> => {
            jest.mocked(useTask).mockReturnValueOnce(
                mockedTaskContextProps({ activeDomains: [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX] })
            );
            const points = [{ x: 30, y: 50, positive: true }];

            const mockedRITMState = mockRITM();
            mockedRITMState.result = {
                shape: { shapeType: ShapeType.RotatedRect, x: 50, y: 50, width: 100, height: 100, angle: 0 },
                points,
            };

            await renderTool();

            await waitFor(() => {
                expect(screen.getByLabelText('result shape', { selector: 'rect' })).toBeVisible();
            });
        });
    });
});
