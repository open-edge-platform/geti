// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getById, getMockedImage } from '../../../../../test-utils/utils';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useAnnotationScene } from '../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import {
    AnnotationToolProvider,
    useAnnotationToolContext,
} from '../../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../../providers/task-chain-provider/task-chain-provider.component';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../zoom/zoom-provider.component';
import {
    defaultAnnotationState,
    notSelectedAnnotation,
    selectedAnnotation,
    selectedHiddenAnnotation,
    selectedLockedAnnotation,
} from '../test-utils';
import { AnnotationListActions } from './annotation-list-actions.component';

jest.mock('../../../providers/task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(),
}));

jest.mock('../../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(),
}));

jest.mock('../../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotation-scene-provider/annotation-scene-provider.component'),
    useAnnotationScene: jest.fn(),
}));

jest.mock('../../../hooks/use-annotator-mode', () => ({
    useAnnotatorMode: jest.fn(() => ({
        isActiveLearningMode: true,
        currentMode: 'active-learning',
    })),
}));

describe('Annotation list actions', () => {
    beforeEach(() => {
        jest.clearAllMocks();

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: defaultAnnotationState,
        }));

        const roi = { x: 0, y: 0, width: 200, height: 200 };
        jest.mocked(useROI).mockReturnValue({
            roi,
            image: getMockedImage(roi),
        });
    });

    const unselectedAnnotations = [
        getMockedAnnotation({ id: '1', isSelected: false }, ShapeType.Rect),
        getMockedAnnotation({ id: '2', zIndex: 1, isSelected: false }),
    ];

    const renderAnnotationListContainer = (annotationToolContext: AnnotationToolContext) => {
        jest.mocked(useAnnotationToolContext).mockImplementation(() => {
            return annotationToolContext;
        });

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: annotationToolContext.scene.annotations,
        }));

        jest.mocked(useAnnotationScene).mockReturnValue(annotationToolContext.scene);

        return render(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <AnnotationToolProvider>
                        <AnnotationListActions />
                    </AnnotationToolProvider>
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    it('Check if there are buttons above annotations when at least one annotation is selected', async () => {
        const annotations = [
            getMockedAnnotation({ id: '1', isSelected: true }, ShapeType.Rect),
            getMockedAnnotation({ id: '2', zIndex: 1, isSelected: false }),
        ];

        const mockToolContext = fakeAnnotationToolContext({
            annotations,
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.getByTestId('annotations-list-select-all')).toBeInTheDocument();
            expect(screen.getByTestId('annotations-list-delete-selected')).toBeInTheDocument();
            expect(screen.getByTestId('annotation-selected-annotations-toggle-visibility')).toBeInTheDocument();
            expect(screen.getByTestId('annotation-selected-annotations-toggle-lock')).toBeInTheDocument();
        });
    });

    it('Check if there are no buttons above annotations when none of the annotations are selected', async () => {
        const mockToolContext = fakeAnnotationToolContext({
            annotations: unselectedAnnotations,
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.queryByTestId('annotations-list-select-all')).toBeInTheDocument();
            expect(screen.queryByTestId('annotations-list-delete-selected')).not.toBeInTheDocument();
            expect(screen.queryByTestId('annotation-selected-annotations-toggle-visibility')).not.toBeInTheDocument();
            expect(screen.queryByTestId('annotation-selected-annotations-toggle-lock')).not.toBeInTheDocument();
        });
    });

    it('Select all annotations and filter annotations buttons are disabled when there are no annotations', async () => {
        const mockToolContext = fakeAnnotationToolContext({
            annotations: [],
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.getByTestId('annotations-list-select-all')).toBeDisabled();
        });
    });

    it('delete selected annotation', async () => {
        const annotations = [getMockedAnnotation({ id: '1', isSelected: true }, ShapeType.Rect)];
        const mockToolContext = fakeAnnotationToolContext({
            annotations,
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.getByTestId('annotations-list-delete-selected')).toBeInTheDocument();
        });

        await userEvent.click(screen.getByTestId('annotations-list-delete-selected'));
        expect(mockToolContext.scene.removeAnnotations).toHaveBeenCalledWith(annotations);
    });

    it('change annotation visibility', async () => {
        const annotation = getMockedAnnotation({ id: '1', isSelected: true, isHidden: false }, ShapeType.Rect);
        const mockToolContext = fakeAnnotationToolContext({
            annotations: [annotation],
        });

        jest.mocked(mockToolContext.scene.setHiddenAnnotations).mockImplementation((...args) => {
            const [fun] = args;
            return fun(annotation);
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.getByTestId('annotation-selected-annotations-toggle-visibility')).toBeInTheDocument();
        });

        await userEvent.click(screen.getByTestId('annotation-selected-annotations-toggle-visibility'));

        expect(mockToolContext.scene.setHiddenAnnotations).toHaveBeenCalledTimes(1);
        expect(mockToolContext.scene.setHiddenAnnotations).toHaveReturnedWith(true);
    });

    it('lock annotation', async () => {
        const annotation = getMockedAnnotation({ id: '1', isSelected: true, isLocked: false }, ShapeType.Rect);
        const mockToolContext = fakeAnnotationToolContext({
            annotations: [annotation],
        });

        jest.mocked(mockToolContext.scene.setLockedAnnotations).mockImplementation((...args) => {
            const [fun] = args;
            return fun(annotation);
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.getByTestId('annotation-selected-annotations-toggle-lock')).toBeInTheDocument();
        });

        await userEvent.click(screen.getByTestId('annotation-selected-annotations-toggle-lock'));

        expect(mockToolContext.scene.setLockedAnnotations).toHaveBeenCalledTimes(1);
        expect(mockToolContext.scene.setLockedAnnotations).toHaveReturnedWith(true);
    });

    it('selects all annotations', async () => {
        const annotation = getMockedAnnotation({ id: '1', isSelected: false, isLocked: false }, ShapeType.Rect);

        const mockToolContext = fakeAnnotationToolContext({
            annotations: [annotation],
        });

        jest.mocked(mockToolContext.scene.setSelectedAnnotations).mockImplementation((...args) => {
            const [fun] = args;
            return fun(annotation);
        });

        await renderAnnotationListContainer(mockToolContext);

        await waitFor(() => {
            expect(screen.getByTestId('annotations-list-select-all')).toBeInTheDocument();
        });

        await userEvent.click(screen.getByTestId('annotations-list-select-all'));

        expect(mockToolContext.scene.setSelectedAnnotations).toHaveBeenCalledTimes(1);
        expect(mockToolContext.scene.setSelectedAnnotations).toHaveReturnedWith(true);
    });

    describe('Changed behaviour - actions take into account state of selected annotations', () => {
        it('lock button has locked status - first selected annotation is locked, second is not locked', async () => {
            const mockToolContext = fakeAnnotationToolContext({
                annotations: [
                    { ...selectedAnnotation, zIndex: 0 },
                    { ...selectedLockedAnnotation, zIndex: 1 },
                ],
            });

            const { container } = await renderAnnotationListContainer(mockToolContext);

            await waitFor(() => {
                const lockIcon = getById(container, 'annotation-selected-annotations-lock-closed-icon');

                expect(lockIcon).toBeInTheDocument();
            });
        });

        it('visibility button has hidden status - first selected annotation is hidden, second is visible', async () => {
            const mockToolContext = fakeAnnotationToolContext({
                annotations: [
                    { ...selectedAnnotation, zIndex: 0 },
                    { ...selectedLockedAnnotation, zIndex: 1 },
                ],
            });

            const { container } = await renderAnnotationListContainer(mockToolContext);

            await waitFor(() => {
                const lockIcon = getById(container, 'annotation-selected-annotations-visibility-on-icon');

                expect(lockIcon).toBeInTheDocument();
            });
        });

        it('select all button is selected when all annotations are selected', async () => {
            const mockToolContext = fakeAnnotationToolContext({
                annotations: [
                    { ...selectedHiddenAnnotation, zIndex: 0 },
                    { ...selectedAnnotation, zIndex: 1 },
                    { ...selectedLockedAnnotation, zIndex: 2 },
                ],
            });

            const { container } = await renderAnnotationListContainer(mockToolContext);

            await waitFor(() => {
                const selectAllCheckbox = getById(container, 'annotations-list-select-all');

                expect(selectAllCheckbox).toBeChecked();
            });
        });

        it('select all button is not selected when all annotations are not selected', async () => {
            const mockToolContext = fakeAnnotationToolContext({
                annotations: defaultAnnotationState,
            });
            await renderAnnotationListContainer(mockToolContext);

            await waitFor(() => {
                const selectAllCheckbox = screen.getByTestId('annotations-list-select-all');

                expect(selectAllCheckbox).not.toBeChecked();
            });
        });

        it('select all button is indeterminate when some annotations are selected and some are not', async () => {
            const mockToolContext = fakeAnnotationToolContext({
                annotations: [
                    { ...selectedHiddenAnnotation, zIndex: 0 },
                    { ...selectedAnnotation, zIndex: 1 },
                    { ...notSelectedAnnotation, zIndex: 2 },
                ],
            });

            await renderAnnotationListContainer(mockToolContext);

            await waitFor(() => {
                const selectAllCheckbox = screen.getByTestId('annotations-list-select-all');

                expect(selectAllCheckbox).toBePartiallyChecked();
            });
        });
    });
});
