// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { SelectedProvider } from '../../../../providers/selected-provider/selected-provider.component';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import { ShapeLabel } from './shape-label.component';

describe('ShapeLabel', () => {
    const renderApp = async (annotation: Annotation) => {
        await annotatorRender(
            <TaskProvider>
                <SelectedProvider>
                    <ShapeLabel annotation={annotation} annotationToolContext={fakeAnnotationToolContext({})} />
                </SelectedProvider>
            </TaskProvider>
        );
    };

    it('render keypoint labels', async () => {
        const label = 'label 1';
        const point = getMockedKeypointNode({ label: getMockedLabel({ id: label, name: label }) });

        await renderApp(
            getMockedAnnotation({
                shape: { shapeType: ShapeType.Pose, points: [point] },
            })
        );

        expect(screen.getByTestId(`pose label - ${label}`)).toBeVisible();
    });

    it('others annotation types', async () => {
        const annotationId = 'test-name';

        await renderApp(getMockedAnnotation({ id: annotationId }));

        expect(screen.getByRole('list')).toHaveAttribute('id', `${annotationId}-labels`);
    });
});
