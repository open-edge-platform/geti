// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import '@wessberg/pointer-events';

import { useRef } from 'react';

import { fireEvent, render, screen } from '@testing-library/react';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { Annotation } from '../../annotation/annotation.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { PointerType } from '../tools.interface';
import { EraserTool } from './eraser-tool.component';

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

describe('EraserTool', () => {
    const PEN_ERASER_BUTTON = {
        pointerType: PointerType.Pen,
        button: 5,
        buttons: 32,
    };

    it('erases annotations', () => {
        const annotations = [
            getMockedAnnotation({
                shape: { shapeType: ShapeType.Circle, x: 100, y: 100, r: 20 },
            }),
        ];
        const annotationToolContext = fakeAnnotationToolContext({
            annotations,
        });

        const App = ({ annotationToolContext: { scene } }: { annotationToolContext: AnnotationToolContext }) => {
            const canvasRef = useRef<SVGSVGElement>(null);

            return (
                <svg ref={canvasRef} width={200} height={200}>
                    <EraserTool scene={scene} annotations={scene.annotations} canvasRef={canvasRef}>
                        {scene.annotations.map((annotation) => (
                            <g data-testid={annotation.id} key={annotation.id}>
                                <Annotation annotation={annotation} />
                            </g>
                        ))}
                    </EraserTool>
                </svg>
            );
        };

        render(<App annotationToolContext={annotationToolContext} />);

        const annotation = screen.getByTestId(annotations[0].id);

        fireEvent.pointerMove(annotation, {
            ...PEN_ERASER_BUTTON,
            clientX: 100,
            clientY: 100,
        });

        expect(annotationToolContext.scene.removeAnnotations).toHaveBeenCalledWith(annotations);
    });
});
