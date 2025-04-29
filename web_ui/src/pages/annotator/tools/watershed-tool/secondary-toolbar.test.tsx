// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useTaskChain } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider, useTask } from '../../providers/task-provider/task-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { BACKGROUND_LABEL } from './utils';
import { useWatershedState, WatershedStateProvider } from './watershed-state-provider.component';

jest.setTimeout(10000);

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../providers/task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../../providers/task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(),
}));

const mockSetBrushSize = jest.fn();

jest.mock('./watershed-state-provider.component', () => ({
    ...jest.requireActual('./watershed-state-provider.component'),
    useWatershedState: jest.fn(() => ({
        shapes: { markers: [], watershedPolygons: [] },
        brushSize: 2,
        setIsBrushSizePreviewVisible: jest.fn(),
        setBrushSize: mockSetBrushSize,
    })),
}));

const mockROI = getMockedROI({ x: 0, y: 0, width: 3000, height: 3000 });
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        labels: [],
        activeDomains: [],
        isTaskChainDomainSelected: jest.fn(),
    })),
}));

const mockLabels = [
    getMockedLabel({ id: '1', name: 'label-1' }),
    getMockedLabel({ id: '2', name: 'label-2' }),
    getMockedLabel({ id: '3', name: 'label-3' }),
];

const defaultToolSettings = { brushSize: 2, sensitivity: 2, label: { label: mockLabels[0], markerId: 2 } };

const getToolSettings = jest.fn().mockReturnValue(defaultToolSettings);

const mockAnnotationToolContext = fakeAnnotationToolContext({
    tool: ToolType.WatershedTool,
    labels: mockLabels,
    getToolSettings,
});

const updateToolSettings = mockAnnotationToolContext.updateToolSettings as jest.Mock;

const renderMockApp = async () =>
    await render(
        <AnnotationSceneProvider annotations={[getMockedAnnotation({})]} labels={[]}>
            <TaskProvider>
                <WatershedStateProvider>
                    <SecondaryToolbar annotationToolContext={mockAnnotationToolContext} />
                </WatershedStateProvider>
            </TaskProvider>
        </AnnotationSceneProvider>
    );

describe('Secondary Toolbar', () => {
    const getAcceptButton = () => screen.queryByLabelText('accept watershed annotation');
    const getRejectButton = () => screen.queryByLabelText('reject watershed annotation');

    beforeEach(() => {
        (useTask as jest.Mock).mockImplementation(() => ({
            selectedTask: null,
            activeDomains: [],
            tasks: [
                {
                    id: '60b609e0d036ba4566726c81',
                    labels: [mockLabels[0]],
                    domain: DOMAIN.CLASSIFICATION,
                    title: 'Classification',
                },
                {
                    id: '60b609e0d036ba4566726c82',
                    labels: [mockLabels[1], mockLabels[2]],
                    domain: DOMAIN.SEGMENTATION,
                    title: 'Segmentation',
                },
            ],
            labels: mockLabels,
        }));

        jest.mocked(useAnnotationToolContext).mockImplementation(() => mockAnnotationToolContext);

        jest.mocked(useTaskChain).mockImplementation(() => ({ inputs: [], outputs: [] }));
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders label picker correctly', async () => {
        await renderMockApp();

        await userEvent.click(screen.getByRole('button', { name: /Select label/i }));

        expect(screen.getByRole('option', { name: BACKGROUND_LABEL.name })).toBeInTheDocument();
        expect(screen.getByDisplayValue(mockLabels[1].name)).toBeInTheDocument();
        expect(screen.getByRole('option', { name: mockLabels[2].name })).toBeInTheDocument();
        expect(screen.queryByText(mockLabels[0].name)).toBeFalsy();
    });

    it('renders sensitivity slider correctly', async () => {
        await renderMockApp();

        // Trigger slider popover
        await userEvent.click(screen.getByTestId('sensitivity-button'));

        const slider = screen.getByRole('slider');

        expect(slider).toBeInTheDocument();

        // Set to minimum
        fireEvent.change(slider, { target: { value: 1 } });

        expect(screen.getByText('1')).toBeInTheDocument();

        // Set to maximum
        fireEvent.change(slider, { target: { value: 5 } });

        expect(screen.getByText('5')).toBeInTheDocument();

        // Trigger onChangeEnd
        fireEvent.keyDown(slider, { key: 'Right' });

        expect(updateToolSettings).toHaveBeenCalledWith(ToolType.WatershedTool, {
            ...defaultToolSettings,
            sensitivity: 5,
        });
    });

    it('renders brush slider correctly', async () => {
        await renderMockApp();

        // Trigger slider popover
        await userEvent.click(screen.getByTestId('brush-size-button'));

        const slider = screen.getByRole('slider');

        expect(screen.getByRole('slider')).toBeInTheDocument();

        fireEvent.change(slider, {
            target: {
                value: 1,
            },
        });

        fireEvent.keyDown(slider, { key: 'Right' });

        expect(mockSetBrushSize).toHaveBeenCalled();
        expect(updateToolSettings).toHaveBeenCalled();
    });

    it('does not render a ButtonGroup if there are no watershed polygons rendered', async () => {
        (useWatershedState as jest.Mock).mockImplementation(() => ({
            shapes: { markers: [], watershedPolygons: [] },
        }));

        await renderMockApp();

        expect(getAcceptButton()).not.toBeInTheDocument();
        expect(getRejectButton()).not.toBeInTheDocument();
    });

    it('renders a ButtonGroup if there are watershed polygons or markers rendered', async () => {
        (useWatershedState as jest.Mock).mockImplementation(() => ({
            shapes: {
                markers: [],
                watershedPolygons: [
                    { id: 1, points: [123, 456] },
                    { id: 2, points: [222, 444] },
                ],
            },
        }));

        await renderMockApp();

        expect(getAcceptButton()).toBeInTheDocument();
        expect(getRejectButton()).toBeInTheDocument();
    });

    it('accepts and rejects annotation correctly', async () => {
        const mockRejectAnnotation = jest.fn();
        const mockSetShapes = jest.fn();

        (useWatershedState as jest.Mock).mockImplementation(() => ({
            shapes: {
                markers: [],
                watershedPolygons: [
                    { id: 1, points: [123, 456] },
                    { id: 2, points: [222, 444] },
                ],
            },
            undoRedoActions: {
                reset: jest.fn(),
            },
            rejectAnnotation: mockRejectAnnotation,
            setShapes: mockSetShapes,
        }));

        await renderMockApp();

        const acceptButton = getAcceptButton();
        const rejectButton = getRejectButton();

        acceptButton && (await userEvent.click(acceptButton));

        expect(mockAnnotationToolContext.scene.addAnnotations).toHaveBeenCalled();

        rejectButton && (await userEvent.click(rejectButton));

        expect(mockRejectAnnotation).toHaveBeenCalled();
    });

    it('disables accept button if there are not polygons to annotate', async () => {
        const mockRejectAnnotation = jest.fn();
        const mockSetShapes = jest.fn();

        (useWatershedState as jest.Mock).mockImplementation(() => ({
            shapes: {
                markers: [{ label: mockLabels[0], points: [123, 456], brushSize: 2, id: 12345 }],
                watershedPolygons: [],
            },
            rejectAnnotation: mockRejectAnnotation,
            setShapes: mockSetShapes,
        }));

        await renderMockApp();

        expect(getAcceptButton()).toHaveAttribute('disabled');
    });

    it('shows only the labels from the supported task', async () => {
        (useTask as jest.Mock).mockImplementation(() => ({
            selectedTask: null,
            activeDomains: [],
            tasks: [
                {
                    id: '60b609e0d036ba4566726c81',
                    labels: [mockLabels[0]],
                    domain: DOMAIN.CLASSIFICATION,
                    title: 'Classification',
                },
                {
                    id: '60b609e0d036ba4566726c82',
                    labels: [mockLabels[1], mockLabels[2]],
                    domain: DOMAIN.SEGMENTATION,
                    title: 'Segmentation',
                },
            ],
        }));

        await renderMockApp();

        await userEvent.click(screen.getByRole('button', { name: /Select label/i }));

        expect(screen.getByRole('option', { name: BACKGROUND_LABEL.name })).toBeInTheDocument();
        expect(screen.getByDisplayValue(mockLabels[1].name)).toBeInTheDocument();
        expect(screen.getByRole('option', { name: mockLabels[2].name })).toBeInTheDocument();
        expect(screen.queryByText(mockLabels[0].name)).toBeFalsy();
    });
});
