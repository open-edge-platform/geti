// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MAX_NUMBER_OF_DISPLAYED_DATASETS } from '../../pages/project-details/components/project-dataset/utils';
import { getMockedDataset } from '../../test-utils/mocked-items-factory/mocked-datasets';
import { pinnedCollapsedReducer } from './reducer';
import { PinnedCollapsedItemsAction } from './use-pinned-collapsed-items.interface';

describe('PinnedCollapsedDatasets reducer', () => {
    const pinnedDatasets = [
        getMockedDataset({ id: 'dataset-1', name: 'Dataset 1' }),
        getMockedDataset({ id: 'dataset-2', name: 'Dataset 2' }),
        getMockedDataset({ id: 'dataset-3', name: 'Dataset 3' }),
        getMockedDataset({ id: 'dataset-4', name: 'Dataset 4' }),
        getMockedDataset({ id: 'dataset-5', name: 'Dataset 5' }),
        getMockedDataset({ id: 'dataset-6', name: 'Dataset 6' }),
    ];

    const collapsedDatasets = [
        getMockedDataset({ id: 'dataset-7', name: 'Dataset 7' }),
        getMockedDataset({ id: 'dataset-8', name: 'Dataset 8' }),
    ];

    const lastPinnedDataset = pinnedDatasets[pinnedDatasets.length - 1];

    it('Should add newly created dataset to pinned datasets - when there are is space in pinned datasets', () => {
        const [dataset1, dataset2, newDataset] = pinnedDatasets;

        expect(
            pinnedCollapsedReducer(MAX_NUMBER_OF_DISPLAYED_DATASETS)(
                { pinnedItems: [dataset1, dataset2], collapsedItems: [] },
                { type: PinnedCollapsedItemsAction.CREATE, payload: newDataset }
            )
        ).toEqual({ collapsedItems: [], pinnedItems: [dataset1, dataset2, newDataset] });
    });

    it('Should replace last pinned dataset with newly created dataset and put last pinned at first position in collapsed', () => {
        const newDataset = getMockedDataset({ id: 'dataset-9', name: 'Dataset 9' });

        expect(
            pinnedCollapsedReducer(MAX_NUMBER_OF_DISPLAYED_DATASETS)(
                { pinnedItems: pinnedDatasets, collapsedItems: collapsedDatasets },
                { type: PinnedCollapsedItemsAction.CREATE, payload: newDataset }
            )
        ).toEqual({
            pinnedItems: [...pinnedDatasets, newDataset].filter(({ id }) => id != lastPinnedDataset.id),
            collapsedItems: [lastPinnedDataset, ...collapsedDatasets],
        });
    });

    it('Should remove dataset from pinned datasets - when there are no collapsed datasets', () => {
        const [dataset1, dataset2, dataset3] = pinnedDatasets;

        expect(
            pinnedCollapsedReducer(MAX_NUMBER_OF_DISPLAYED_DATASETS)(
                { pinnedItems: [dataset1, dataset2, dataset3], collapsedItems: [] },
                { type: PinnedCollapsedItemsAction.REMOVE, payload: { id: dataset2.id } }
            )
        ).toEqual({
            collapsedItems: [],
            pinnedItems: [dataset1, dataset3],
        });
    });

    it('Should remove dataset from pinned datasets and put first dataset from collapsed datasets to last position of pinned datasets', () => {
        const pinnedDataset = pinnedDatasets[2];
        const firstDatasetFromCollapsedDatasets = collapsedDatasets[0];

        expect(
            pinnedCollapsedReducer(MAX_NUMBER_OF_DISPLAYED_DATASETS)(
                { pinnedItems: pinnedDatasets, collapsedItems: collapsedDatasets },
                { type: PinnedCollapsedItemsAction.REMOVE, payload: { id: pinnedDataset.id } }
            )
        ).toEqual({
            pinnedItems: [...pinnedDatasets, firstDatasetFromCollapsedDatasets].filter(
                ({ id }) => id != pinnedDataset.id
            ),
            collapsedItems: collapsedDatasets.filter(({ id }) => id != firstDatasetFromCollapsedDatasets.id),
        });
    });

    it('Should update name of the dataset', () => {
        const pinnedDataset = pinnedDatasets[2];
        const newName = 'New dataset name';

        expect(
            pinnedCollapsedReducer(MAX_NUMBER_OF_DISPLAYED_DATASETS)(
                { pinnedItems: pinnedDatasets, collapsedItems: collapsedDatasets },
                { type: PinnedCollapsedItemsAction.UPDATE, payload: { id: pinnedDataset.id, name: newName } }
            )
        ).toEqual({
            pinnedItems: pinnedDatasets.map((dataset) =>
                dataset.id == pinnedDataset.id ? { ...dataset, name: newName } : dataset
            ),
            collapsedItems: collapsedDatasets,
        });
    });

    it('Should swap first dataset from collapsed datasets with selected dataset from pinned datasets', () => {
        const selectedCollapsedDataset = collapsedDatasets[0];

        expect(
            pinnedCollapsedReducer(MAX_NUMBER_OF_DISPLAYED_DATASETS)(
                { pinnedItems: pinnedDatasets, collapsedItems: collapsedDatasets },
                { type: PinnedCollapsedItemsAction.SWAP, payload: { id: selectedCollapsedDataset.id } }
            )
        ).toEqual({
            pinnedItems: [...pinnedDatasets, selectedCollapsedDataset].filter(({ id }) => id != lastPinnedDataset.id),
            collapsedItems: [lastPinnedDataset, ...collapsedDatasets].filter(
                ({ id }) => id != selectedCollapsedDataset.id
            ),
        });
    });
});
