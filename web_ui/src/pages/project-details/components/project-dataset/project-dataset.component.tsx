// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useMemo } from 'react';

import { Flex, Item, TabPanels, Tabs } from '@adobe/react-spectrum';

import { Dataset } from '../../../../core/projects/dataset.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useDataset } from '../../../../providers/dataset-provider/dataset-provider.component';
import { TutorialCardBuilder } from '../../../../shared/components/tutorial-card/tutorial-card-builder.component';
import { hasEqualId } from '../../../../shared/utils';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { DatasetTabList } from './dataset-tab-list.component';
import { DatasetTabPanel } from './dataset-tab-panel.component';

import classes from './project-dataset.module.scss';

/*
    We display MAX_NUMBER_OF_DISPLAYED_DATASETS tabs and once we have more datasets
    we populate the picker with the extra datasets.
    So basically if the user adds MAX_NUMBER_OF_DISPLAYED_DATASETS datasets, we display all in tabs.
    But if the user adds one more, we will show MAX_NUMBER_OF_DISPLAYED_DATASETS dataset tabs and move the extra
    datasets to the Picker. The new dataset is placed at the end of pinned datasets.
*/
export const ProjectDataset = (): JSX.Element => {
    const { isSingleDomainProject } = useProject();
    const { pinnedDatasets, handleSelectDataset, selectedDataset } = useDataset();

    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);
    const hasSelectedPinnedDataset = pinnedDatasets.find(hasEqualId(selectedDataset.id)) !== undefined;

    const items = useMemo(() => {
        return pinnedDatasets.map((dataset) => {
            return {
                id: `dataset-${dataset.id}-id`,
                key: dataset.id,
                name: dataset.name,
                dataset,
            };
        });
    }, [pinnedDatasets]);

    return (
        <Flex direction={'column'} UNSAFE_className={classes.componentWrapper} height={'100%'}>
            {isAnomalyProject && (
                <TutorialCardBuilder
                    cardKey={TUTORIAL_CARD_KEYS.ANOMALY_TUTORIAL}
                    styles={{ fontSize: 'var(--spectrum-global-dimension-font-size-350)' }}
                />
            )}
            <Tabs
                items={items}
                height='100%'
                orientation={'vertical'}
                minHeight={0}
                UNSAFE_className={!hasSelectedPinnedDataset ? classes.noneSelected : ''}
                aria-label='Dataset page tabs'
                selectedKey={selectedDataset.id}
                onSelectionChange={(key: Key) => handleSelectDataset(String(key))}
            >
                <DatasetTabList />

                <TabPanels height={'100%'} minHeight={0}>
                    {(item: { dataset: Dataset }) => (
                        <Item textValue={item.dataset.name}>
                            <DatasetTabPanel dataset={item.dataset} />
                        </Item>
                    )}
                </TabPanels>
            </Tabs>
        </Flex>
    );
};
