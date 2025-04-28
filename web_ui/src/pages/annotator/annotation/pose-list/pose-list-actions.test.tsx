// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { KeypointAnnotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { SelectedProvider } from '../../../../providers/selected-provider/selected-provider.component';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { AnnotationToolProvider } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { AnnotatorProviders } from '../../test-utils/annotator-render';
import { OCCLUDE_TOOLTIP, PoseListActions, VISIBLE_TOOLTIP } from './pose-list-actions.component';

const mockedUpdateAnnotation = jest.fn();
jest.mock('../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-scene-provider/annotation-scene-provider.component'),
    useAnnotationScene: () => ({
        annotations: [],
        updateAnnotation: mockedUpdateAnnotation,
    }),
}));

const renderApp = async ({
    items,
    selected = [],
}: {
    items: { name: string; isVisible?: boolean }[];
    selected?: string[];
}) => {
    const mockedAnnotation = getMockedAnnotation({
        shape: {
            shapeType: ShapeType.Pose,
            points: items.map(({ name, isVisible = true }) => ({
                x: 0,
                y: 0,
                edgeEnds: [],
                isVisible,
                label: labelFromUser(getMockedLabel({ id: name, name })),
            })),
        },
    }) as KeypointAnnotation;

    providersRender(
        <AnnotatorProviders datasetIdentifier={getMockedDatasetIdentifier()}>
            <AnnotationToolProvider>
                <SelectedProvider selectedIds={selected}>
                    <PoseListActions keypointAnnotation={mockedAnnotation} />
                </SelectedProvider>
            </AnnotationToolProvider>
        </AnnotatorProviders>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
};

describe('PoseListActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('select checkbox', () => {
        it('select all items when no items have been selected initially', async () => {
            await renderApp({ items: [{ name: 'label 1' }, { name: 'label 2' }] });

            fireEvent.click(screen.getByRole('checkbox', { name: '0 out of 2 points selected' }));

            expect(screen.getByRole('checkbox', { name: '2 out of 2 points selected' })).toBeVisible();
        });

        it('deselect all items when some items were previously selected', async () => {
            await renderApp({
                selected: ['label 1'],
                items: [{ name: 'label 1' }, { name: 'label 2' }],
            });

            fireEvent.click(screen.getByRole('checkbox', { name: '1 out of 2 points selected' }));

            expect(screen.getByRole('checkbox', { name: '0 out of 2 points selected' })).toBeVisible();
        });
    });

    describe('occlude items', () => {
        const getButtonSelector = () => screen.getByRole('button', { name: 'visibility toggle' });
        const selectAllItems = (total: number) => {
            return screen.getByRole('checkbox', { name: `0 out of ${total} points selected` });
        };

        it(' disable the button when no items are selected', async () => {
            await renderApp({
                items: [{ name: 'label 1' }, { name: 'label 2' }],
            });

            expect(getButtonSelector()).toBeDisabled();
        });

        it('hide all elements when all elements were previously visible', async () => {
            const items = [
                { name: 'label 1', isVisible: true },
                { name: 'label 2', isVisible: true },
            ];
            await renderApp({ items });

            fireEvent.click(selectAllItems(items.length));
            fireEvent.click(getButtonSelector());

            await checkTooltip(getButtonSelector(), OCCLUDE_TOOLTIP);

            expect(mockedUpdateAnnotation).toHaveBeenCalledWith(
                expect.objectContaining({
                    shape: expect.objectContaining({
                        points: expect.arrayContaining([expect.objectContaining({ isVisible: false })]),
                    }),
                })
            );
        });

        it('display all elements when some elements were previously hidden', async () => {
            const items = [
                { name: 'label 1', isVisible: false },
                { name: 'label 2', isVisible: true },
            ];

            await renderApp({ items });

            fireEvent.click(selectAllItems(items.length));
            fireEvent.click(getButtonSelector());

            await checkTooltip(getButtonSelector(), VISIBLE_TOOLTIP);

            expect(mockedUpdateAnnotation).toHaveBeenCalledWith(
                expect.objectContaining({
                    shape: expect.objectContaining({
                        points: expect.arrayContaining([expect.objectContaining({ isVisible: true })]),
                    }),
                })
            );
        });

        it('display all items when all items were previously hidden', async () => {
            const items = [
                { name: 'label 1', isVisible: false },
                { name: 'label 2', isVisible: false },
            ];

            await renderApp({ items });

            fireEvent.click(selectAllItems(items.length));
            fireEvent.click(getButtonSelector());

            await checkTooltip(getButtonSelector(), VISIBLE_TOOLTIP);

            expect(mockedUpdateAnnotation).toHaveBeenCalledWith(
                expect.objectContaining({
                    shape: expect.objectContaining({
                        points: expect.arrayContaining([expect.objectContaining({ isVisible: true })]),
                    }),
                })
            );
        });
    });
});
