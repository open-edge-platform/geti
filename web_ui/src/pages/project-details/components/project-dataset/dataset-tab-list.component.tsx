// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Flex, Item, Loading, TabList, Tooltip, TooltipTrigger } from '@geti/ui';
import { Add } from '@geti/ui/icons';

import { Dataset } from '../../../../core/projects/dataset.interface';
import { useDataset } from '../../../../providers/dataset-provider/dataset-provider.component';
import { CollapsedItemsPicker } from '../../../../shared/components/collapsed-items-picker/collapsed-items-picker.component';
import { TabItem } from '../../../../shared/components/tabs/tabs.interface';
import { hasEqualId } from '../../../../shared/utils';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ProjectDatasetTabActions } from './project-dataset-tab-actions.component';
import { useSelectedDataset } from './use-selected-dataset/use-selected-dataset.hook';
import { MAX_NUMBER_OF_DISPLAYED_DATASETS } from './utils';

import classes from './project-dataset.module.scss';

export const DatasetTabList = () => {
    const selectedDataset = useSelectedDataset();
    const { project } = useProject();

    const numberOfDatasets = project.datasets.length;

    const { createDataset, pinnedDatasets, collapsedDatasets, handleCreateDataset, handleSelectDataset } = useDataset();

    const hasSelectedPinnedDataset = pinnedDatasets.find(hasEqualId(selectedDataset.id)) !== undefined;
    const collapsedPickerItems = collapsedDatasets.map(({ id, name }) => ({ id, name }));

    return (
        <Flex
            alignItems={'center'}
            width={'100%'}
            position={'relative'}
            id={`dataset-${selectedDataset.id}`}
            UNSAFE_className={classes.tabWrapper}
        >
            <TabList UNSAFE_className={classes.tabList}>
                {(item: TabItem & { dataset: Dataset }) => (
                    <Item textValue={String(item.dataset.name)} key={item.dataset.id}>
                        <ProjectDatasetTabActions dataset={item.dataset} />
                    </Item>
                )}
            </TabList>

            {numberOfDatasets > MAX_NUMBER_OF_DISPLAYED_DATASETS ? (
                <CollapsedItemsPicker
                    items={collapsedPickerItems}
                    ariaLabel={'Collapsed datasets'}
                    onSelectionChange={handleSelectDataset}
                    hasSelectedPinnedItem={hasSelectedPinnedDataset}
                    numberOfCollapsedItems={collapsedDatasets.length}
                />
            ) : null}

            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    id='create-dataset-button-id'
                    onPress={handleCreateDataset}
                    isDisabled={createDataset.isPending}
                    aria-label={'Create dataset'}
                >
                    {createDataset.isPending ? <Loading mode='inline' size='S' /> : <Add color='white' />}
                </ActionButton>
                <Tooltip>Create new testing set</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
