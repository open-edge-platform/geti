// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, within } from '@testing-library/react';

import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { Label, LABEL_BEHAVIOUR } from '../../../../../core/labels/label.interface';
import { isGlobal } from '../../../../../core/labels/utils';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, getMockedLabels } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { mockedProjectContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { checkTooltip, getById, hover } from '../../../../../test-utils/utils';
import { ToolType } from '../../../core/annotation-tool-context.interface';
import { renderApp, renderAppWithDefaultLabel } from './tests/renders';

jest.mock('../../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => mockedProjectContextProps({})),
}));

jest.mock('../../../../../core/labels/utils', () => ({
    ...jest.requireActual('../../../../../core/labels/utils'),
    isGlobal: jest.fn(() => jest.requireActual('../../../../../core/labels/utils').isGlobal),
}));

describe('Label shortcuts', () => {
    const labels2 = getMockedLabels(2);
    const labels3 = getMockedLabels(3);
    const labels6 = getMockedLabels(6);
    const labels8 = getMockedLabels(8);
    const labels10 = getMockedLabels(10);
    const labelCard1 = getMockedLabel({ id: '123', name: 'card 1' });

    beforeEach(() => {
        global.localStorage.clear();
        jest.restoreAllMocks();

        Element.prototype.scrollIntoView = jest.fn();
    });

    afterAll(() => {
        jest.clearAllTimers();
    });

    const getMoreButton = (): HTMLElement | null => screen.queryByRole('button', { name: 'More more-icon' });

    const clickMoreButton = () => {
        const moreButton = getMoreButton();
        moreButton && fireEvent.click(moreButton);
    };

    it('Show 3 labels - More button should not be visible', async () => {
        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels: labels3,
        });

        expect(screen.getAllByRole('button')).toHaveLength(3);
        expect(getMoreButton()).not.toBeInTheDocument();
    });

    it('6 labels - show 5 labels - More button should be visible', async () => {
        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels: labels6,
        });

        const moreButton = getMoreButton();
        expect(screen.getAllByRole('button')).toHaveLength(6);
        expect(moreButton).toBeInTheDocument();
    });

    it('8 labels - show 5 and rest under more option', async () => {
        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels: labels8,
        });

        expect(screen.getAllByRole('button')).toHaveLength(6);
        expect(screen.queryAllByRole('listitem')).toHaveLength(5);
        clickMoreButton();
        expect(screen.getAllByRole('listitem')).toHaveLength(5 + 8);
    });

    it('pin two more labels (test 6, test 7)', async () => {
        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels: labels8,
        });

        // Initially we have 5 pinned buttons
        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(5);

        clickMoreButton();

        hover(screen.getByText('test-7'));
        fireEvent.click(screen.getByRole('button', { name: '7-pin-icon' }));

        hover(screen.getByText('test-6'));
        fireEvent.click(screen.getByRole('button', { name: '6-pin-icon' }));

        // 3 pinned buttons have been removed
        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(7);
        expect(screen.queryAllByRole('button', { name: /test-/i }).map((label) => label.id)).toStrictEqual([
            'label-1',
            'label-2',
            'label-3',
            'label-4',
            'label-5',
            'label-7',
            'label-6',
        ]);
    });

    it('unpin labels: test 2, test 1 and test 3', async () => {
        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels: labels8,
        });

        // Initially we have 5 pinned buttons
        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(5);

        clickMoreButton();

        fireEvent.click(screen.getByRole('button', { name: '1-unpin-icon' }));
        fireEvent.click(screen.getByRole('button', { name: '2-unpin-icon' }));
        fireEvent.click(screen.getByRole('button', { name: '3-unpin-icon' }));
        // 2 pinned, 8 unpinned
        expect(screen.getAllByRole('listitem')).toHaveLength(2 + 8);
        expect(within(screen.getByLabelText(/label search results/i)).getAllByRole('listitem')).toHaveLength(8);

        // 3 pinned buttons have been removed
        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(2);
    });

    it('unpin labels: test 2, test 1 and test 5 then pin test 5 and test 1', async () => {
        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels: labels8,
        });

        // Initially we have 5 pinned buttons
        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(5);

        clickMoreButton();

        fireEvent.click(screen.getByRole('button', { name: '2-unpin-icon' }));
        fireEvent.click(screen.getByRole('button', { name: '1-unpin-icon' }));
        fireEvent.click(screen.getByRole('button', { name: '5-unpin-icon' }));

        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(2);

        hover(screen.getByText('test-5'));
        fireEvent.click(screen.getByRole('button', { name: '5-pin-icon' }));

        hover(screen.getByText('test-1'));
        fireEvent.click(screen.getByRole('button', { name: '1-pin-icon' }));

        expect(screen.queryAllByRole('button', { name: /test-/i }).map((label) => label.id)).toStrictEqual([
            'label-3',
            'label-4',
            'label-5',
            'label-1',
        ]);
    });

    it('Click shortcut - addLabel should be called', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});

        await renderApp({
            annotations: [getMockedAnnotation({ id: '1', isSelected: true, labels: [] }, ShapeType.Polygon)],
            labels: labels2,
            addLabel: annotationToolContext.scene.addLabel,
        });

        fireEvent.click(screen.getByRole('button', { name: 'test-1' }));
        expect(annotationToolContext.scene.addLabel).toHaveBeenCalled();
    });

    it('Clicking "empty label" twice removes the annotation', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});

        const emptyLabel: Label = getMockedLabel({
            id: '321',
            color: '#000',
            name: 'Empty',
            group: 'Empty',
            isEmpty: true,
        });
        const normalLabel = getMockedLabel({ name: 'normal label' });
        const mockedAnnotation = getMockedAnnotation(
            { id: '1', isSelected: true, labels: [{ ...emptyLabel, source: { userId: 'userId' } }] },
            ShapeType.Rect
        );

        await renderApp({
            annotations: [mockedAnnotation],
            labels: [normalLabel, emptyLabel],
            removeAnnotations: annotationToolContext.scene.removeAnnotations,
        });

        fireEvent.click(screen.getByRole('button', { name: emptyLabel.name }));
        expect(annotationToolContext.scene.removeAnnotations).toHaveBeenCalledWith([mockedAnnotation]);
    });

    it('Clicking "empty label" with a selected local annotation removes the label', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});

        const emptyLabel: Label = getMockedLabel({
            id: '321',
            color: '#000',
            name: 'Empty',
            group: 'Empty',
            isEmpty: true,
        });
        const normalLabel = getMockedLabel({ name: 'normal label' });
        const mockedAnnotation = getMockedAnnotation(
            {
                id: '1',
                isSelected: true,
                labels: [
                    { ...emptyLabel, source: { userId: 'userId' } },
                    { ...getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL }), source: { userId: 'id-1' } },
                ],
            },
            ShapeType.Rect
        );

        await renderApp({
            annotations: [mockedAnnotation],
            labels: [normalLabel, emptyLabel],
            removeLabels: annotationToolContext.scene.removeLabels,
            removeAnnotations: annotationToolContext.scene.removeAnnotations,
        });

        fireEvent.click(screen.getByRole('button', { name: emptyLabel.name }));
        expect(annotationToolContext.scene.removeAnnotations).not.toHaveBeenCalled();
        expect(annotationToolContext.scene.removeLabels).toHaveBeenCalledWith([emptyLabel], [mockedAnnotation.id]);
    });

    it('Click shortcut of already added label - removeLabel should be called', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});
        const annotations = [
            getMockedAnnotation(
                {
                    id: '1',
                    isSelected: true,
                    labels: [{ ...labels2[0], source: { userId: 'id-1' } }],
                },
                ShapeType.Polygon
            ),
        ];

        await renderApp({
            annotations,
            labels: labels2,
            addLabel: annotationToolContext.scene.addLabel,
            removeLabels: annotationToolContext.scene.removeLabels,
        });

        fireEvent.click(screen.getByRole('button', { name: 'test-1' }));
        expect(annotationToolContext.scene.removeLabels).toHaveBeenCalled();
        expect(annotationToolContext.scene.addLabel).not.toHaveBeenCalled();
    });

    it('Check tooltip on hover', async () => {
        const twoMockedLabels = getMockedLabels(2, ['ctrl+1', 'ctrl+2']);
        const annotations = [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)];

        await renderApp({ annotations, labels: twoMockedLabels });

        await checkTooltip(screen.getByRole('button', { name: 'test-1' }), 'test-1 (CTRL+1)');
    });

    it('Select shortcut without selected annotation - nothing happens', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});
        const labels = [...getMockedLabels(2), getMockedLabel({ id: '3', name: 'No object', isExclusive: true })];

        await renderApp({ annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)], labels });

        fireEvent.click(screen.getByRole('button', { name: 'test-1' }));
        expect(annotationToolContext.scene.addLabel).not.toHaveBeenCalled();
        expect(annotationToolContext.scene.removeLabels).not.toHaveBeenCalled();
    });

    it('Select empty label shortcut without selected annotation - should set it on image', async () => {
        const emptyLabel = getMockedLabel({ id: '3', name: 'No object', isExclusive: true });
        const labels = [...getMockedLabels(2), emptyLabel];
        const annotationToolContext = fakeAnnotationToolContext({});

        await renderApp({
            annotations: [getMockedAnnotation({ id: '1' }, ShapeType.Polygon)],
            labels,
            addLabel: annotationToolContext.scene.addLabel,
            removeLabels: annotationToolContext.scene.removeLabels,
        });

        fireEvent.click(screen.getByRole('button', { name: 'No object' }));
        expect(annotationToolContext.scene.addLabel).toHaveBeenCalledWith(emptyLabel, []);
        expect(annotationToolContext.scene.removeLabels).not.toHaveBeenCalled();
    });

    it('Select 3 annotations and click label shortcut - all of them should have label set', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});
        const annotations = [
            getMockedAnnotation({ id: '1', isSelected: true }, ShapeType.Polygon),
            getMockedAnnotation({ id: '2', isSelected: true }, ShapeType.Circle),
            getMockedAnnotation({ id: '3', isSelected: true }, ShapeType.Rect),
        ];

        await renderApp({ annotations, labels: labels10, addLabel: annotationToolContext.scene.addLabel });

        fireEvent.click(screen.getByRole('button', { name: labels3[0].name }));
        expect(annotationToolContext.scene.addLabel).toHaveBeenCalledWith(labels3[0], ['1', '2', '3']);
    });

    it('Select 3 annotations and click label shortcut (one of annotations has that label already) - all of them should have label set', async () => {
        const annotations = [
            getMockedAnnotation(
                {
                    id: '1',
                    isSelected: true,
                    labels: [{ ...labels3[0], source: { userId: '123321' } }],
                },
                ShapeType.Polygon
            ),
            getMockedAnnotation({ id: '2', isSelected: true }, ShapeType.Circle),
            getMockedAnnotation({ id: '3', isSelected: true }, ShapeType.Rect),
        ];
        const annotationToolContext = fakeAnnotationToolContext({});

        await renderApp({ annotations, labels: labels3, addLabel: annotationToolContext.scene.addLabel });

        fireEvent.click(screen.getByRole('button', { name: labels3[0].name }));
        expect(annotationToolContext.scene.addLabel).toHaveBeenCalledWith(labels3[0], ['1', '2', '3']);
    });

    it('Select 3 annotations and click label shortcut (all of annotations has that label already) - all of them should have label removed', async () => {
        const annotations = [
            getMockedAnnotation(
                {
                    id: '1',
                    isSelected: true,
                    labels: [{ ...labels3[0], source: { userId: '123321' } }],
                },
                ShapeType.Polygon
            ),
            getMockedAnnotation(
                {
                    id: '2',
                    isSelected: true,
                    labels: [{ ...labels3[0], source: { userId: '123321' } }],
                },
                ShapeType.Circle
            ),
            getMockedAnnotation(
                {
                    id: '3',
                    isSelected: true,
                    labels: [{ ...labels3[0], source: { userId: '123321' } }],
                },
                ShapeType.Rect
            ),
        ];
        const annotationToolContext = fakeAnnotationToolContext({});

        await renderApp({ annotations, labels: labels3, removeLabels: annotationToolContext.scene.removeLabels });

        fireEvent.click(screen.getByRole('button', { name: labels3[0].name }));
        expect(annotationToolContext.scene.removeLabels).toHaveBeenCalledWith([labels3[0]], ['1', '2', '3']);
    });

    it('Clicking multiple times on "Anomalous" labels does not removes it', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});
        const anomalousLabel = getMockedLabel({ id: '3', name: 'Anomalous', behaviour: LABEL_BEHAVIOUR.ANOMALOUS });

        await renderApp({
            annotations: [
                getMockedAnnotation(
                    { id: '1', labels: [{ ...anomalousLabel, source: { userId: '123321' } }], isSelected: true },
                    ShapeType.Polygon
                ),
            ],
            labels: [anomalousLabel],
        });

        fireEvent.click(screen.getByRole('button', { name: anomalousLabel.name }));
        expect(annotationToolContext.scene.addLabel).not.toHaveBeenCalled();
        expect(annotationToolContext.scene.removeLabels).not.toHaveBeenCalled();
        expect(annotationToolContext.scene.removeAnnotations).not.toHaveBeenCalled();
    });

    it('Clicking multiple times on exclusive labels does not removes it', async () => {
        const annotationToolContext = fakeAnnotationToolContext({});
        const anomalousLabel = getMockedLabel({
            id: '3',
            name: 'Normal',
            behaviour: LABEL_BEHAVIOUR.EXCLUSIVE,
            isExclusive: true,
        });

        await renderApp({
            annotations: [
                getMockedAnnotation(
                    { id: '1', labels: [{ ...anomalousLabel, source: { userId: '123321' } }], isSelected: true },
                    ShapeType.Polygon
                ),
            ],
            labels: [anomalousLabel],
        });

        fireEvent.click(screen.getByRole('button', { name: anomalousLabel.name }));
        expect(annotationToolContext.scene.addLabel).not.toHaveBeenCalled();
        expect(annotationToolContext.scene.removeLabels).not.toHaveBeenCalled();
        expect(annotationToolContext.scene.removeAnnotations).not.toHaveBeenCalled();
    });

    describe('default label', () => {
        const annotations = [
            getMockedAnnotation(
                {
                    id: '1',
                    isSelected: true,
                    labels: [{ ...labels3[0], source: { userId: '123321' } }],
                },
                ShapeType.Polygon
            ),
        ];

        const labels = [
            getMockedLabel({ id: 'label-1', name: 'label-1', behaviour: LABEL_BEHAVIOUR.LOCAL }),
            getMockedLabel({ id: 'label-2', name: 'label-2', behaviour: LABEL_BEHAVIOUR.LOCAL }),
            getMockedLabel({ id: 'label-3', name: 'label-3', behaviour: LABEL_BEHAVIOUR.LOCAL }),
            getMockedLabel({
                id: 'empty-label',
                name: 'empty-label',
                behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE,
            }),
        ];

        it('sets the default label', async () => {
            await renderAppWithDefaultLabel(annotations, labels);

            const label = screen.getByLabelText('Default label');

            fireEvent.click(screen.getByRole('button', { name: labels[0].name }));
            expect(label).toHaveTextContent(labels[0].id);

            fireEvent.click(screen.getByRole('button', { name: labels[1].name }));
            expect(label).toHaveTextContent(labels[1].id);

            fireEvent.click(screen.getByRole('button', { name: labels[2].name }));
            expect(label).toHaveTextContent(labels[2].id);

            // It does not set the default label to an empty label
            fireEvent.click(screen.getByRole('button', { name: labels[3].name }));
            expect(label).toHaveTextContent(labels[2].id);
        });

        it('sets the default label when using a smart tool', async () => {
            await renderAppWithDefaultLabel(annotations, labels);

            const label = screen.getByLabelText('Default label');

            fireEvent.click(screen.getByRole('button', { name: labels[0].name }));
            expect(label).toHaveTextContent(labels[0].id);

            fireEvent.click(screen.getByRole('button', { name: labels[1].name }));
            expect(label).toHaveTextContent(labels[1].id);

            fireEvent.click(screen.getByRole('button', { name: labels[2].name }));
            expect(label).toHaveTextContent(labels[2].id);

            // It does not set the default label to an empty label
            fireEvent.click(screen.getByRole('button', { name: labels[3].name }));
            expect(label).toHaveTextContent(labels[2].id);
        });
    });

    it('Render "No object" labels without color.', async () => {
        const noObjectLabel = getMockedLabel({
            id: '123',
            color: '#000',
            name: 'No object',
            group: 'No object',
            isEmpty: true,
        });
        const noClassLabel = getMockedLabel({
            id: '321',
            color: '#000',
            name: 'No class',
            group: 'No class',
            isEmpty: true,
        });
        const normalLabel = getMockedLabel({ name: 'normal label' });
        const { container } = await renderApp({ annotations: [], labels: [noObjectLabel, noClassLabel, normalLabel] });

        // TODO: change these 2 expects to "No object" and "No class" once backend updates their code
        expect(screen.getByText('No object')).toBeVisible();
        expect(screen.getByText('No class')).toBeVisible();
        expect(getById(container, `${noObjectLabel.id}-color-thumb-label-item`)).toBeNull();
        expect(getById(container, `${noClassLabel.id}-color-thumb-label-item`)).toBeNull();
        expect(getById(container, `${normalLabel.id}-color-thumb-label-item`)).toBeVisible();
    });

    it('Ignores unknown labels from localstorage', async () => {
        // Setup the localstorage so that it contains a label id that does not exist,
        global.localStorage.setItem(
            'pinnedLabels_undefined_Segmentation',
            JSON.stringify(['non-existing-id', ...labels8.map(({ id }) => id)])
        );

        await renderApp({ annotations: [], labels: labels8 });

        // Verify that all other labels are properly shown
        expect(screen.queryAllByRole('button', { name: /test-/i })).toHaveLength(8);
    });

    it.each([ToolType.GrabcutTool, ToolType.RITMTool, ToolType.SSIMTool, ToolType.SegmentAnythingTool])(
        'calls smartTool handler with %s',
        async (tool) => {
            const mockedAddLabel = jest.fn();
            const mockedUpdateToolSettings = jest.fn();

            await renderApp({
                tool,
                annotations: [],
                isDrawing: true,
                labels: [labelCard1],
                addLabel: mockedAddLabel,
                updateToolSettings: mockedUpdateToolSettings,
            });

            fireEvent.click(screen.getByRole('button', { name: labelCard1.name }));

            expect(mockedAddLabel).not.toHaveBeenCalled();
            expect(mockedUpdateToolSettings).toHaveBeenCalledWith(tool, {
                selectedLabel: labelCard1,
            });
        }
    );

    describe('anomaly projects', () => {
        it.each([ToolType.GrabcutTool, ToolType.RITMTool, ToolType.SSIMTool, ToolType.SegmentAnythingTool])(
            'calls regular handler with %s',
            async (tool) => {
                const mockedAddLabel = jest.fn();
                const mockedUpdateToolSettings = jest.fn();

                await renderApp({
                    tool,
                    annotations: [],
                    isDrawing: true,
                    labels: [labelCard1],
                    domain: DOMAIN.ANOMALY_DETECTION,
                    addLabel: mockedAddLabel,
                    updateToolSettings: mockedUpdateToolSettings,
                });

                fireEvent.click(screen.getByRole('button', { name: labelCard1.name }));

                expect(isGlobal).toHaveBeenCalledWith(labelCard1);
                expect(mockedAddLabel).toHaveBeenCalledWith(labelCard1, []);
                expect(mockedUpdateToolSettings).not.toHaveBeenCalled();
            }
        );
    });
});
