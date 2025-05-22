// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useMemo } from 'react';

import { Item, Picker, Text } from '@geti/ui';

import { Dataset } from '../../../../../../core/projects/dataset.interface';
import { isAnomalyDomain } from '../../../../../../core/projects/domains';
import { useNavigateToAnnotatorRoute } from '../../../../../../core/services/use-navigate-to-annotator-route.hook';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';
import { useSelectedDataset } from '../../../../../project-details/components/project-dataset/use-selected-dataset/use-selected-dataset.hook';
import { useProject } from '../../../../../project-details/providers/project-provider/project-provider.component';
import { useDataset } from '../../../../providers/dataset-provider/dataset-provider.component';

const ACTIVE_DATASET_ID = '1';

const getSelectedKey = (isInActiveMode: boolean, selectedDataset: Dataset, trainingDatasetId: string) => {
    if (isInActiveMode) {
        return ACTIVE_DATASET_ID;
    }

    if (selectedDataset.id === trainingDatasetId) {
        return 'dataset';
    }

    return selectedDataset.id;
};

export const DatasetPicker = (): JSX.Element => {
    const { project, projectIdentifier, isSingleDomainProject } = useProject();
    const { isInActiveMode } = useDataset();
    const navigateToAnnotatorRoute = useNavigateToAnnotatorRoute();
    const selectedDataset = useSelectedDataset();

    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);

    const [trainingDataset, ...testingDatasets] = project.datasets.map((dataset) => ({
        key: dataset.id,
        text: dataset.name,
    }));

    const datasetItems = useMemo(() => {
        const items = [
            { key: ACTIVE_DATASET_ID, text: 'Active set' },
            // We set the key for the 'Training dataset' to 'dataset' so that the e2e tests will pass
            { key: 'dataset', text: trainingDataset.text },
            ...testingDatasets,
        ];

        // Anomaly projects should not contain 'Active set'
        if (isAnomalyProject) {
            items.shift();
        }

        return items;
    }, [isAnomalyProject, testingDatasets, trainingDataset.text]);

    const handleChangeDataset = (key: Key) => {
        // Selecting 'Active dataset' doesn't change the current dataset, it just
        // changes the endpoint where we get the media items from.
        if (key === ACTIVE_DATASET_ID) {
            navigateToAnnotatorRoute({
                datasetIdentifier: { ...projectIdentifier, datasetId: trainingDataset.key },
                active: true,
            });
        } else {
            // Due to the e2e tests the key for the training dataset set in the picker is set to `dataset-id`
            // in this case we want to use navigate to the training dataset's id
            const datasetId = key === 'dataset' ? trainingDataset.key : (key as string);

            navigateToAnnotatorRoute({
                datasetIdentifier: { ...projectIdentifier, datasetId },
                active: false,
            });
        }
    };

    const selectedKey = getSelectedKey(isInActiveMode, selectedDataset, trainingDataset.key);

    return (
        <Picker
            width={{ base: 'auto', s: 'size-1000' }}
            id={'selected-annotation-dataset-id'}
            data-testid={'selected-annotation-dataset-id'}
            aria-label='Choose annotation dataset'
            UNSAFE_style={{ fontWeight: 'bold' }}
            isQuiet
            items={datasetItems}
            selectedKey={selectedKey}
            onSelectionChange={handleChangeDataset}
        >
            {(item) => (
                <Item key={item.key} textValue={item.text}>
                    <Text id={`${idMatchingFormat(item.key)}-id`}>{item.text}</Text>
                </Item>
            )}
        </Picker>
    );
};
