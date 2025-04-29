// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { getMockedDatasetIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender } from '../../../../../test-utils/project-provider-render';
import { AnnotatorProviders } from '../../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../zoom/zoom-provider.component';
import { ClosestKeypoint } from './closest-keypoint.component';

const movePoint = (element: HTMLElement, newPoint: Point) => {
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
};

const mockedNodes = [
    getMockedKeypointNode({ label: getMockedLabel({ id: 'label-1' }), x: 10, y: 10 }),
    getMockedKeypointNode({ label: getMockedLabel({ id: 'label-2' }), x: 20, y: 20 }),
    getMockedKeypointNode({ label: getMockedLabel({ id: 'label-3' }), x: 30, y: 30 }),
];

describe('ClosestKeypoint', () => {
    const renderApp = async (nodes: KeypointNode[], onClosestElement = jest.fn()) => {
        projectRender(
            <AnnotatorProviders datasetIdentifier={getMockedDatasetIdentifier()}>
                <ZoomProvider>
                    <TransformZoomAnnotation>
                        <ClosestKeypoint
                            nodes={nodes}
                            data-testid='closest-keypoint'
                            onClosestElement={onClosestElement}
                        >
                            {(closestElement) => <p>{closestElement?.label.id}</p>}
                        </ClosestKeypoint>
                    </TransformZoomAnnotation>
                </ZoomProvider>
            </AnnotatorProviders>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('updates closest element on pointer move', async () => {
        const [node1, node2] = mockedNodes;
        const onClosestElement = jest.fn();

        await renderApp(mockedNodes, onClosestElement);

        const svgElement = screen.getByTestId('closest-keypoint');

        movePoint(svgElement, { x: 10, y: 10 });
        expect(screen.getByText(node1.label.id)).toBeVisible();
        expect(onClosestElement).toHaveBeenLastCalledWith(node1);

        movePoint(svgElement, { x: 22, y: 22 });
        expect(screen.getByText(node2.label.id)).toBeVisible();
        expect(onClosestElement).toHaveBeenLastCalledWith(node2);
    });

    it('updates the element on hover', async () => {
        const [node1] = mockedNodes;

        await renderApp(mockedNodes);

        const svgElement = screen.getByTestId('closest-keypoint');

        movePoint(svgElement, { x: node1.x, y: node1.y });
        expect(screen.getByText(node1.label.id)).toBeVisible();
    });
});
