// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { SelectedProvider } from '../../providers/selected-provider/selected-provider.component';
import { NodeContent } from './node-content.component';

const mockedSetHovered = jest.fn();
jest.mock('../../providers/hovered-provider/hovered-provider.component', () => ({
    useSetHoveredId: () => mockedSetHovered,
}));

jest.mock('../../hooks/use-annotator-mode', () => ({
    useAnnotatorMode: jest.fn(() => ({
        isActiveLearningMode: true,
    })),
}));

const renderApp = (point?: Partial<KeypointNode> & { label?: Partial<AnnotationLabel> }) => {
    render(
        <SelectedProvider>
            <NodeContent isLast={false} onUpdate={jest.fn()} point={getMockedKeypointNode(point)} />
        </SelectedProvider>
    );
};

describe('NodeContent', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('grid', () => {
        it('hover action', () => {
            const labelId = 'mocked-label-id';
            renderApp({ label: getMockedLabel({ id: labelId, color: '#fff' }) });

            fireEvent.mouseEnter(screen.getByRole('listitem'));
            expect(mockedSetHovered).toHaveBeenLastCalledWith(labelId);

            fireEvent.mouseLeave(screen.getByRole('listitem'));
            expect(mockedSetHovered).toHaveBeenLastCalledWith(null);
        });
    });

    describe('checkbox area', () => {
        it('select the point', () => {
            const labelName = 'label3';
            renderApp({ label: getMockedLabel({ id: labelName, name: labelName, color: '#fff' }) });

            const checkbox = screen.getByRole('checkbox', { name: `Select keypoint ${labelName}` });

            expect(checkbox).not.toBeChecked();
            fireEvent.click(checkbox);

            expect(screen.getByText(labelName)).toBeVisible();
            expect(checkbox).toBeChecked();
        });

        it('hidden with on PREDICTION mode', () => {
            jest.mocked(useAnnotatorMode).mockReturnValueOnce({
                isActiveLearningMode: false,
                currentMode: ANNOTATOR_MODE.PREDICTION,
            });

            const labelName = 'label3';

            renderApp({ label: getMockedLabel({ id: labelName, name: labelName, color: '#fff' }) });

            expect(screen.queryByRole('checkbox', { name: `Select keypoint ${labelName}` })).not.toBeInTheDocument();
        });
    });

    describe('color area', () => {
        it('colorSwatch is visible', () => {
            renderApp({ isVisible: true });

            expect(screen.getByLabelText(/label color/i)).toBeVisible();
            expect(screen.queryByLabelText('occluded icon')).not.toBeInTheDocument();
        });

        it('occluded icon is visible', () => {
            renderApp({ isVisible: false });

            expect(screen.getByLabelText('occluded icon')).toBeVisible();
            expect(screen.queryByLabelText(/label color/i)).not.toBeInTheDocument();
        });
    });

    describe('label name', () => {
        it('annotation', () => {
            const labelName = 'label test';

            renderApp({ label: getMockedLabel({ id: labelName, name: labelName, color: '#fff' }) });

            expect(screen.getByText(labelName)).toBeVisible();
            expect(screen.queryByTestId('prediction label container')).not.toBeInTheDocument();
        });

        it('prediction', () => {
            const labelName = 'label test';

            renderApp({
                label: {
                    ...getMockedLabel({ id: labelName, name: labelName, color: '#fff' }),
                    score: 0.5,
                    source: { userId: undefined },
                },
            });

            expect(screen.getByTestId('prediction label container')).toBeVisible();
            expect(screen.getByText('(50%)')).toBeVisible();
            expect(screen.getByText(labelName)).toBeVisible();
            expect(screen.getByLabelText('prediction icon')).toBeVisible();
        });
    });

    describe('ListMenu', () => {
        it('displays the menu trigger hovering', () => {
            renderApp({ label: getMockedLabel({ name: 'label test', color: '#fff' }) });

            fireEvent.mouseEnter(screen.getByRole('listitem'));

            expect(screen.queryByRole('button', { name: 'menu trigger' })).toBeVisible();
        });

        it('hidden the menu trigger on PREDICTION mode', () => {
            jest.mocked(useAnnotatorMode).mockReturnValueOnce({
                isActiveLearningMode: false,
                currentMode: ANNOTATOR_MODE.PREDICTION,
            });

            renderApp({ label: getMockedLabel({ name: 'label test', color: '#fff' }) });

            fireEvent.mouseEnter(screen.getByRole('listitem'));

            expect(screen.queryByRole('button', { name: 'menu trigger' })).not.toBeInTheDocument();
        });
    });
});
