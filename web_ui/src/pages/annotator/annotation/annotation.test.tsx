// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render } from '@testing-library/react';

import { AnnotationLabel, Annotation as AnnotationType } from '../../../core/annotations/annotation.interface';
import { Polygon as PolygonShape } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { labelFromModel, labelFromUser } from '../../../core/annotations/utils';
import { HoveredProvider } from '../../../providers/hovered-provider/hovered-provider.component';
import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { DEFAULT_ANNOTATION_STYLES, EDIT_ANNOTATION_STYLES } from '../tools/utils';
import { Annotation } from './annotation.component';

describe('Annotation components', () => {
    it('Draws a rectangle', () => {
        const shape = { shapeType: ShapeType.Rect, x: 0, y: 10, width: 100, height: 110 } as const;
        const annotation: AnnotationType = getMockedAnnotation({ shape }, ShapeType.Rect);

        const { container } = render(
            <svg>
                <Annotation annotation={annotation} />
            </svg>
        );
        const rect = container.querySelector('rect');

        expect(rect).toHaveAttribute('x', `${shape.x}`);
        expect(rect).toHaveAttribute('y', `${shape.y}`);
        expect(rect).toHaveAttribute('width', `${shape.width}`);
        expect(rect).toHaveAttribute('height', `${shape.height}`);
    });

    it('Draws a circle', () => {
        const shape = { shapeType: ShapeType.Circle, x: 0, y: 10, r: 33 } as const;
        const annotation: AnnotationType = getMockedAnnotation({ shape }, ShapeType.Circle);

        const { container } = render(
            <svg>
                <Annotation annotation={annotation} />
            </svg>
        );
        const circle = container.querySelector('circle');

        expect(circle).toHaveAttribute('cx', `${shape.x}`);
        expect(circle).toHaveAttribute('cy', `${shape.y}`);
        expect(circle).toHaveAttribute('r', `${shape.r}`);
    });

    it('Draws a polygon', () => {
        const shape: PolygonShape = {
            shapeType: ShapeType.Polygon,
            points: [
                { x: 0, y: 0 },
                { x: 10, y: 0 },
                { x: 10, y: 10 },
            ],
        };
        const annotation: AnnotationType = getMockedAnnotation({ shape }, ShapeType.Polygon);

        const { container } = render(
            <svg>
                <Annotation annotation={annotation} />
            </svg>
        );
        const polygon = container.querySelector('polygon');

        const points = shape.points;
        expect(polygon).toHaveAttribute(
            'points',
            `${points[0].x},${points[0].y} ${points[1].x},${points[1].y} ${points[2].x},${points[2].y}`
        );
    });

    describe('Labelling', () => {
        const shape = { shapeType: ShapeType.Rect, x: 0, y: 10, width: 100, height: 110 } as const;
        const otherLabel = labelFromUser(getMockedLabel({ color: 'blue' }));
        const label = labelFromUser(getMockedLabel({ color: 'red' }));

        it('gives a background color based on its labels', () => {
            const labels: AnnotationLabel[] = [otherLabel, label];
            const annotation: AnnotationType = getMockedAnnotation({ shape, labels }, ShapeType.Rect);

            const { container } = render(
                <svg>
                    <Annotation annotation={annotation} />
                </svg>
            );
            const rect = container.querySelector('g');

            expect(rect).toHaveAttribute('fill', label.color);
            expect(rect).toHaveAttribute('stroke', label.color);
        });

        it('applies the default Intel Geti color to annotations without labels', () => {
            const annotation: AnnotationType = getMockedAnnotation({ shape, labels: [] }, ShapeType.Rect);

            const { container } = render(
                <svg>
                    <Annotation annotation={annotation} />
                </svg>
            );
            const rect = container.querySelector('g');

            expect(rect).toHaveAttribute('fill', DEFAULT_ANNOTATION_STYLES.fill);
            expect(rect).toHaveAttribute('stroke', DEFAULT_ANNOTATION_STYLES.stroke);
            expect(rect).toHaveAttribute('stroke-dasharray', '0');
        });

        it('applies selected stroke color when an annotation is selected', () => {
            const labels: AnnotationLabel[] = [otherLabel, label];
            const annotation: AnnotationType = getMockedAnnotation({ shape, labels, isSelected: true }, ShapeType.Rect);

            const { container } = render(
                <svg>
                    <Annotation annotation={annotation} />
                </svg>
            );
            const rect = container.querySelector('g');

            expect(rect).toHaveAttribute('fill', label.color);
            expect(rect).toHaveAttribute('stroke', EDIT_ANNOTATION_STYLES.stroke);
        });

        it('applies selected stroke color when an annotation is hovered', () => {
            const labels: AnnotationLabel[] = [otherLabel, label];
            const annotation: AnnotationType = getMockedAnnotation({ shape, labels }, ShapeType.Rect);

            const { container } = render(
                <HoveredProvider hoveredId={annotation.id}>
                    <svg>
                        <Annotation annotation={annotation} />
                    </svg>
                </HoveredProvider>
            );
            const rect = container.querySelector('g');

            expect(rect).toHaveAttribute('fill', label.color);
            expect(rect).toHaveAttribute('stroke', EDIT_ANNOTATION_STYLES.stroke);
        });

        it('applies strokeDasharray on prediction mode', () => {
            const annotation: AnnotationType = getMockedAnnotation(
                { shape, labels: [otherLabel, label] },
                ShapeType.Rect
            );

            const { container } = render(
                <svg>
                    <Annotation annotation={annotation} isPredictionMode />
                </svg>
            );
            const rect = container.querySelector('g');

            expect(rect).toHaveAttribute('stroke-dasharray', '10 6');
        });

        it('applies svg background on prediction', () => {
            const labelColor = 'red';
            const predictionLabel = labelFromModel(
                getMockedLabel({ name: 'label-1', id: 'label-1', behaviour: 2, color: labelColor }),
                0.8,
                '212',
                '212'
            );

            const annotation: AnnotationType = getMockedAnnotation(
                { shape, labels: [otherLabel, predictionLabel] },
                ShapeType.Rect
            );

            const { container } = render(
                <svg>
                    <Annotation annotation={annotation} />
                </svg>
            );
            const rect = container.querySelector('g');
            const patternId = `#${annotation.id}-pattern`;
            const pattern = container.querySelector(patternId);

            expect(rect).toHaveAttribute(`fill`, `url(${patternId}) ${labelColor}`);
            expect(pattern).toBeVisible();
        });
    });
});
