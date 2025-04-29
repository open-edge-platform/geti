// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { labelFromUser } from '../../../../../core/annotations/utils';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { usePrediction } from '../../../providers/prediction-provider/prediction-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { AnnotationListCounting } from './annotation-list-counting.component';

jest.mock('../../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

jest.mock('../../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../../providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(() => ({ predictionAnnotations: [] })),
}));

describe('AnnotationListCounting', () => {
    it('should show the number of all annotations next to the title', async () => {
        const mockedLabels = [getMockedLabel({ id: 'tree-item-1' })];
        const mockAnnotations: Annotation[] = [
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0])],
            }),
        ];

        const fakeContext = fakeAnnotationToolContext({
            annotations: mockAnnotations,
        });
        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [getMockedTask({ labels: mockedLabels })] })
        );

        await render(<AnnotationListCounting annotationToolContext={fakeContext} />);

        expect(screen.getByTestId('all-labels-count-id')).toHaveTextContent('3');
    });

    it('should render a labelTreeView with the correct number of annotations per label', async () => {
        const mockedLabels = [
            getMockedLabel({ id: 'tree-item-1', name: 'tree-item-1' }),
            getMockedLabel({ id: 'tree-item-2', name: 'tree-item-2' }),
            getMockedLabel({ id: 'tree-item-3', name: 'tree-item-3' }),
        ];
        const mockAnnotations: Annotation[] = [
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0]), labelFromUser(mockedLabels[1])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[2])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0]), labelFromUser(mockedLabels[1])],
            }),
        ];

        const fakeContext = fakeAnnotationToolContext({
            annotations: mockAnnotations,
        });

        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [getMockedTask({ labels: mockedLabels })] })
        );

        await render(<AnnotationListCounting annotationToolContext={fakeContext} />);

        expect(screen.getByLabelText('annotation label count tree-item-1')).toHaveTextContent('3');
        expect(screen.getByLabelText('annotation label count tree-item-2')).toHaveTextContent('2');
        expect(screen.getByLabelText('annotation label count tree-item-3')).toHaveTextContent('1');
    });

    it('should show counts for predictions', async () => {
        const mockedLabels = [
            getMockedLabel({ id: 'tree-item-1', name: 'tree-item-1' }),
            getMockedLabel({ id: 'tree-item-2', name: 'tree-item-2' }),
            getMockedLabel({ id: 'tree-item-3', name: 'tree-item-3' }),
        ];
        const mockAnnotations: Annotation[] = [
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0]), labelFromUser(mockedLabels[1])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[2])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0])],
            }),
            getMockedAnnotation({
                labels: [labelFromUser(mockedLabels[0]), labelFromUser(mockedLabels[1])],
            }),
        ];

        const fakeContext = fakeAnnotationToolContext({
            annotations: [],
        });

        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [getMockedTask({ labels: mockedLabels })] })
        );

        // @ts-expect-error we only mock predictions
        jest.mocked(usePrediction).mockReturnValue({
            predictionAnnotations: mockAnnotations,
        });

        await render(<AnnotationListCounting annotationToolContext={fakeContext} />, {
            initialEntries: ['?mode=predictions'],
        });

        expect(screen.getByLabelText('annotation label count tree-item-1')).toHaveTextContent('3');
        expect(screen.getByLabelText('annotation label count tree-item-2')).toHaveTextContent('2');
        expect(screen.getByLabelText('annotation label count tree-item-3')).toHaveTextContent('1');
    });
});
