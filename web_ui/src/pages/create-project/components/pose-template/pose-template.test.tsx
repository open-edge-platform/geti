// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, screen } from '@testing-library/react';

import '@testing-library/jest-dom/extend-expect';

import { annotatorRender } from '../../../annotator/test-utils/annotator-render';
import { MIN_POINTS_MESSAGE } from '../../utils';
import { EMPTY_POINT_MESSAGE } from './empty-point-message.component';
import { PoseTemplate, PoseTemplateProps } from './pose-template.component';

const addPoint = (mouseEventInit: MouseEventInit) => {
    const drawingBox = screen.getByLabelText('drawing box');
    const pointerupEvent = new MouseEvent('pointerup', { ...mouseEventInit, bubbles: true, cancelable: true });

    act(() => {
        drawingBox.dispatchEvent(pointerupEvent);
    });
};

describe('PoseTemplate', () => {
    const renderApp = async ({
        animationDirection = 0,
        updateProjectState = jest.fn(),
        metadata = [],
    }: Partial<PoseTemplateProps>) => {
        await annotatorRender(
            <PoseTemplate
                metadata={metadata}
                animationDirection={animationDirection}
                updateProjectState={updateProjectState}
            />
        );
    };

    beforeEach(() => {
        SVGElement.prototype.releasePointerCapture = jest.fn();
    });

    describe('error messages', () => {
        it('message is visible', async () => {
            await renderApp({});

            expect(screen.getByTestId('info-section')).toBeInTheDocument();
            expect(screen.getByText(MIN_POINTS_MESSAGE)).toBeInTheDocument();
        });
    });

    it('updates projectTypeMetadata after state updates', async () => {
        const mockUpdateProjectState = jest.fn();
        await renderApp({ updateProjectState: mockUpdateProjectState });

        addPoint({ clientX: 100, clientY: 100 });

        expect(mockUpdateProjectState).toHaveBeenLastCalledWith({
            projectTypeMetadata: [
                expect.objectContaining({
                    labels: expect.arrayContaining([expect.objectContaining({ name: '1' })]),
                    keypointStructure: {
                        edges: [],
                        positions: [{ label: '1', x: 0.1, y: 0.1 }],
                    },
                }),
            ],
        });
    });

    it('add points message is not visible when there are points', async () => {
        await renderApp({});

        expect(screen.queryByText(EMPTY_POINT_MESSAGE)).toBeInTheDocument();

        addPoint({ clientX: 150, clientY: 75 });

        expect(screen.queryByText(EMPTY_POINT_MESSAGE)).not.toBeInTheDocument();
    });
});
