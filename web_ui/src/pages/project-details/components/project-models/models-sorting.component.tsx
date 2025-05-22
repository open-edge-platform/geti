// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key } from 'react';

import { Icon, Item, Menu, MenuTrigger, Section, Text } from '@geti/ui';
import { SortDown, SortUp, SortUpDown } from '@geti/ui/icons';

import { ModelGroupsAlgorithmDetails } from '../../../../core/models/models.interface';
import {
    sortModelsGroupsByActiveModel,
    sortModelsGroupsByComplexity,
    sortModelsGroupsByCreationTime,
    sortModelsGroupsByModelSize,
    sortModelsGroupsByScore,
} from '../../../../core/models/utils';
import { SortDirection } from '../../../../core/shared/query-parameters';
import { ButtonWithSpectrumTooltip } from '../../../../shared/components/button-with-tooltip/button-with-tooltip.component';

export enum ModelsSortingOptions {
    ACTIVE_MODEL_ASC = 'Active model (asc)',
    ACTIVE_MODEL_DESC = 'Active model (desc)',
    CREATION_TIME_ASC = 'Creation time (asc)',
    CREATION_TIME_DESC = 'Creation time (desc)',
    SCORE_ASC = 'Score (asc)',
    SCORE_DESC = 'Score (desc)',
    SIZE_ASC = 'Size (asc)',
    SIZE_DESC = 'Size (desc)',
    COMPLEXITY_ASC = 'Complexity (asc)',
    COMPLEXITY_DESC = 'Complexity (desc)',
}

export const MODEL_SORTING_FUNCTIONS: Record<
    ModelsSortingOptions,
    (modelsGroups: ModelGroupsAlgorithmDetails[]) => ModelGroupsAlgorithmDetails[]
> = {
    [ModelsSortingOptions.SCORE_ASC]: (modelsGroups) => sortModelsGroupsByScore(modelsGroups, SortDirection.ASC),
    [ModelsSortingOptions.SCORE_DESC]: (modelsGroups) => sortModelsGroupsByScore(modelsGroups, SortDirection.DESC),
    [ModelsSortingOptions.COMPLEXITY_ASC]: (modelsGroups) =>
        sortModelsGroupsByComplexity(modelsGroups, SortDirection.ASC),
    [ModelsSortingOptions.COMPLEXITY_DESC]: (modelsGroups) =>
        sortModelsGroupsByComplexity(modelsGroups, SortDirection.DESC),
    [ModelsSortingOptions.CREATION_TIME_ASC]: (modelsGroups) =>
        sortModelsGroupsByCreationTime(modelsGroups, SortDirection.ASC),
    [ModelsSortingOptions.CREATION_TIME_DESC]: (modelsGroups) =>
        sortModelsGroupsByCreationTime(modelsGroups, SortDirection.DESC),
    [ModelsSortingOptions.SIZE_ASC]: (modelsGroups) => sortModelsGroupsByModelSize(modelsGroups, SortDirection.ASC),
    [ModelsSortingOptions.SIZE_DESC]: (modelsGroups) => sortModelsGroupsByModelSize(modelsGroups, SortDirection.DESC),
    [ModelsSortingOptions.ACTIVE_MODEL_ASC]: (modelsGroups) =>
        sortModelsGroupsByActiveModel(modelsGroups, SortDirection.ASC),
    [ModelsSortingOptions.ACTIVE_MODEL_DESC]: (modelsGroups) =>
        sortModelsGroupsByActiveModel(modelsGroups, SortDirection.DESC),
};

const ModelsSortingMenu: FC<{ selectedSortingOption: ModelsSortingOptions; onSort: (key: Key) => void }> = ({
    onSort,
    selectedSortingOption,
}) => {
    return (
        <Menu selectionMode={'single'} defaultSelectedKeys={[selectedSortingOption]} onAction={onSort}>
            {[
                [ModelsSortingOptions.ACTIVE_MODEL_ASC, ModelsSortingOptions.ACTIVE_MODEL_DESC],
                [ModelsSortingOptions.CREATION_TIME_ASC, ModelsSortingOptions.CREATION_TIME_DESC],
                [ModelsSortingOptions.SCORE_ASC, ModelsSortingOptions.SCORE_DESC],
                [ModelsSortingOptions.SIZE_ASC, ModelsSortingOptions.SIZE_DESC],
                [ModelsSortingOptions.COMPLEXITY_ASC, ModelsSortingOptions.COMPLEXITY_DESC],
            ].map(([asc, desc]) => {
                return (
                    <Section key={asc}>
                        <Item key={asc} textValue={asc}>
                            <Text>{asc.replace(' (asc)', '')}</Text>
                            <Icon>
                                <SortUp />
                            </Icon>
                        </Item>
                        <Item key={desc} textValue={desc}>
                            <Text>{desc.replace(' (desc)', '')}</Text>
                            <Icon>
                                <SortDown />
                            </Icon>
                        </Item>
                    </Section>
                );
            })}
        </Menu>
    );
};

export const ModelsSorting: FC<{ selectedSortingOption: ModelsSortingOptions; onSort: (key: Key) => void }> = ({
    onSort,
    selectedSortingOption,
}) => {
    return (
        <MenuTrigger>
            <ButtonWithSpectrumTooltip aria-label={'Sort models'} isQuiet tooltip={'Models sorting'}>
                <SortUpDown />
            </ButtonWithSpectrumTooltip>
            <ModelsSortingMenu selectedSortingOption={selectedSortingOption} onSort={onSort} />
        </MenuTrigger>
    );
};
