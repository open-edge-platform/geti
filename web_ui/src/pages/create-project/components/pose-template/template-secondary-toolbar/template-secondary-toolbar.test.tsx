// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { useSelected } from '../../../../../providers/selected-provider/selected-provider.component';
import { KeyMap } from '../../../../../shared/keyboard-events/keyboard.interface';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender } from '../../../../../test-utils/required-providers-render';
import { EdgeLine } from '../util';
import {
    nodeConnectionMessage,
    nodeInteractionMessage,
    TemplateSecondaryToolbar,
} from './template-secondary-toolbar.component';

jest.mock('../../../../../providers/selected-provider/selected-provider.component', () => ({
    useSelected: jest.fn(),
}));

describe('TemplateSecondaryToolbar', () => {
    const renderApp = ({
        edges = [],
        points = [],
        isSelected = true,
        isDeleteNodeEnabled = true,
        mockOnStateUpdate = jest.fn(),
    }: {
        color?: string;
        edges?: EdgeLine[];
        points?: KeypointNode[];
        isSelected?: boolean;
        isDeleteNodeEnabled?: boolean;
        mockOnStateUpdate?: jest.Mock;
    }) => {
        jest.mocked(useSelected).mockReturnValue({
            isSelected: jest.fn().mockReturnValue(isSelected),
            addSelected: jest.fn(),
            removeSelected: jest.fn(),
            setSelected: jest.fn(),
        });

        const initialState = {
            edges,
            points,
        };
        providersRender(
            <TemplateSecondaryToolbar
                state={initialState}
                onStateUpdate={mockOnStateUpdate}
                isDeleteNodeEnabled={isDeleteNodeEnabled}
            />
        );
    };

    it('renders empty if no point is selected', () => {
        renderApp({ isSelected: false });

        expect(screen.queryByLabelText('label name input')).not.toBeInTheDocument();
    });

    it('renders the label color correctly', () => {
        renderApp({
            points: [
                getMockedKeypointNode({
                    label: getMockedLabel({ id: '1', name: '1', color: '#ffffff' }),
                }),
            ],
        });

        expect(screen.getByLabelText('white, color selector')).toBeVisible();
    });

    it('updated label name when the label input field is changed', () => {
        const mockOnStateUpdate = jest.fn();
        const point1 = getMockedKeypointNode({
            label: getMockedLabel({ id: '1', name: '1', color: '#000000' }),
        });
        const point2 = getMockedKeypointNode({
            label: getMockedLabel({ id: '2', name: '2', color: '#ffffff' }),
        });
        const edge = { id: '123', from: point1, to: point2 };

        renderApp({ edges: [edge], points: [point1, point2], mockOnStateUpdate });

        const input = screen.getByLabelText('label name input');
        fireEvent.change(input, { target: { value: 'New Label' } });

        const updatedPoint = {
            ...point1,
            label: { ...point1.label, name: 'New Label' },
        };
        expect(mockOnStateUpdate).toHaveBeenCalledWith({
            edges: [{ id: edge.id, from: updatedPoint, to: point2 }],
            points: [updatedPoint, point2],
            skipHistory: true,
        });
    });

    it('call onStateUpdate when delete button is pressed', () => {
        const mockOnStateUpdate = jest.fn();
        const point = getMockedKeypointNode({
            label: getMockedLabel({ id: '1', name: '1', color: '#ffffff' }),
        });

        renderApp({ points: [point], mockOnStateUpdate });

        fireEvent.click(screen.getByRole('button', { name: 'toolbar delete keypoint 1' }));
        expect(mockOnStateUpdate).toHaveBeenCalledWith({ points: [], edges: [], skipHistory: false });
    });

    describe('no point is selected', () => {
        it('connection message is visible', () => {
            renderApp({ isSelected: false, isDeleteNodeEnabled: true });

            expect(screen.queryByLabelText('label name input')).not.toBeInTheDocument();
            expect(screen.queryByText(nodeConnectionMessage)).toBeVisible();
        });

        it('interaction message is visible', () => {
            renderApp({ isSelected: false, isDeleteNodeEnabled: false });

            expect(screen.queryByLabelText('label name input')).not.toBeInTheDocument();
            expect(screen.queryByText(nodeInteractionMessage)).toBeVisible();
        });
    });

    describe('hotkeys', () => {
        const point = getMockedKeypointNode({
            label: getMockedLabel({ id: '1', name: '1', color: '#ffffff' }),
        });
        const point2 = getMockedKeypointNode({
            label: getMockedLabel({ id: '2', name: '2', color: '#ffffff' }),
        });
        const edge = { id: '123', from: point, to: point2 };

        const renderAndAssertEmptyState = ({
            keyMap,
            edges = [],
            points = [],
        }: {
            keyMap: KeyMap;
            edges?: EdgeLine[];
            points?: KeypointNode[];
        }) => {
            const mockOnStateUpdate = jest.fn();
            renderApp({ points, edges, isSelected: true, mockOnStateUpdate });

            fireEvent.keyDown(document, { key: keyMap, code: keyMap });

            expect(mockOnStateUpdate).toHaveBeenCalledWith({ points: [], edges: [], skipHistory: false });
        };
        describe('Backspace', () => {
            it('remove point', async () => {
                renderAndAssertEmptyState({ keyMap: KeyMap.Backspace, points: [point] });
            });

            it('remove edge', async () => {
                renderAndAssertEmptyState({ keyMap: KeyMap.Backspace, edges: [edge] });
            });
        });

        describe('Delete', () => {
            it('remove point', async () => {
                renderAndAssertEmptyState({ keyMap: KeyMap.Delete, points: [point] });
            });

            it('remove edge', async () => {
                renderAndAssertEmptyState({ keyMap: KeyMap.Delete, edges: [edge] });
            });
        });
    });

    describe('delete button', () => {
        it('hides it when deletion is disabled', () => {
            const mockOnStateUpdate = jest.fn();
            const point = getMockedKeypointNode({ label: getMockedLabel({ id: '1', name: '1', color: '#ffffff' }) });

            renderApp({ points: [point], mockOnStateUpdate, isDeleteNodeEnabled: false });

            expect(screen.queryByRole('button', { name: 'toolbar delete keypoint 1' })).not.toBeInTheDocument();
        });

        it('enable/disable when shift is pressed', () => {
            const point = getMockedKeypointNode({ label: getMockedLabel({ id: '1', name: '1', color: '#ffffff' }) });

            renderApp({ points: [point] });

            fireEvent.keyDown(document.body, { key: 'Shift', code: 'ShiftLeft' });
            expect(screen.getByRole('button', { name: 'toolbar delete keypoint 1' })).toBeDisabled();

            fireEvent.keyUp(document.body, { key: 'Shift', code: 'ShiftLeft' });
            expect(screen.getByRole('button', { name: 'toolbar delete keypoint 1' })).toBeEnabled();
        });
    });
});
