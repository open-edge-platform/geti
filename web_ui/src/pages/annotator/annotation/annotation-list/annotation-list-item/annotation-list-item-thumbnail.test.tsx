// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { Rect } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { getMockedImage } from '../../../../../test-utils/utils';
import { AnnotationListItemThumbnail } from './annotation-list-item-thumbnail.component';

jest.mock('../../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({ isTaskChainProject: false })),
}));

describe('Annotations list item thumbnail', () => {
    const mockShape = { shapeType: ShapeType.Rect, x: 0, y: 0, height: 100, width: 100 } as Rect;
    const mockImage = getMockedImage();

    it('renders a canvas with correctly', async () => {
        render(
            <AnnotationListItemThumbnail
                image={mockImage}
                annotationShape={mockShape}
                annotationId={'test-annotation'}
                onSelectAnnotation={jest.fn()}
                isSelected={false}
            />
        );

        expect(screen.queryByTestId('annotation-test-annotation-thumbnail')).toBeTruthy();
    });

    it('renders a canvas with the correct dimensions passed as props', () => {
        render(
            <AnnotationListItemThumbnail
                image={mockImage}
                annotationShape={mockShape}
                annotationId={'test-annotation'}
                isSelected={false}
                onSelectAnnotation={jest.fn()}
                width={40}
                height={40}
            />
        );

        expect(screen.getByTestId('annotation-test-annotation-thumbnailWrapper')).toHaveStyle(
            'width: 40px; height: 40px'
        );
    });

    it('renders a canvas with a blue border if the annotation is selected', () => {
        render(
            <AnnotationListItemThumbnail
                image={mockImage}
                annotationShape={mockShape}
                onSelectAnnotation={jest.fn()}
                annotationId={'test-annotation'}
                isSelected
            />
        );

        expect(screen.getByTestId('annotation-test-annotation-thumbnailWrapper')).toHaveClass('isSelected');
    });

    it('shows an annotation status indicator', async () => {
        render(
            <AnnotationListItemThumbnail
                image={mockImage}
                annotationShape={mockShape}
                annotationId={'test-annotation'}
                onSelectAnnotation={jest.fn()}
                isSelected={false}
                status={MEDIA_ANNOTATION_STATUS.ANNOTATED}
            />
        );

        expect(screen.queryByTestId('annotation-test-annotation-thumbnail')).toBeTruthy();
        expect(screen.getByLabelText('Annotated')).toBeInTheDocument();
    });
});
