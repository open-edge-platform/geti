// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { Content, ContextualHelp, Heading, Item, Picker, Section } from '@geti-ui/ui';

import { DatasetSource, useTrainModelState } from './train-model-provider.component';

const SECTION_TITLES: Record<DatasetSource['kind'], string> = {
    current: 'Current dataset',
    view: 'Dataset views',
    revision: 'Dataset revisions',
};

export const SelectDatasetRevision = () => {
    const { datasetSources, selectedDatasetSourceId, onSelectDatasetSourceId } = useTrainModelState();

    const sections = useMemo(
        () =>
            (['current', 'view', 'revision'] as const)
                .map((kind) => ({
                    id: kind,
                    name: SECTION_TITLES[kind],
                    children: datasetSources.filter((source) => source.kind === kind),
                }))
                .filter(({ children }) => children.length > 0),
        [datasetSources]
    );

    return (
        <Picker
            flex={1}
            items={sections}
            label={'Select dataset'}
            data-testid={'select-dataset'}
            selectedKey={selectedDatasetSourceId}
            onSelectionChange={(key) => onSelectDatasetSourceId(String(key))}
            contextualHelp={
                <ContextualHelp variant={'info'} placement={'top'}>
                    <Heading>Selecting a dataset</Heading>
                    <Content>
                        {`Choose the data to use for training. Select "Use current dataset" to train on the most recent
                        version of all the data (what you see in the "Dataset" page). Select a dataset view to train
                        only on the media assigned to that view. Select a dataset revision to train on the exact same
                        data (media and annotations) as another model.`}
                    </Content>
                </ContextualHelp>
            }
        >
            {(section) => (
                <Section key={section.id} title={section.name} items={section.children}>
                    {(item) => <Item key={item.id}>{item.name}</Item>}
                </Section>
            )}
        </Picker>
    );
};
