// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key } from 'react';

import { Icon, Item, Menu, MenuTrigger, Section, Text } from '@adobe/react-spectrum';

import { SortDown, SortUp, SortUpDown } from '../../../../assets/icons';
import { ModelGroupsAlgorithmDetails } from '../../../../core/models/models.interface';
import {
    sortModelsGroupsByActiveModel,
    sortModelsGroupsByComplexity,
    sortModelsGroupsByCreationTime,
    sortModelsGroupsByModelSize,
    sortModelsGroupsByScore,
} from '../../../../core/models/utils';
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
    [ModelsSortingOptions.SCORE_ASC]: (modelsGroups) => sortModelsGroupsByScore(modelsGroups, 'ASC'),
    [ModelsSortingOptions.SCORE_DESC]: (modelsGroups) => sortModelsGroupsByScore(modelsGroups, 'DESC'),
    [ModelsSortingOptions.COMPLEXITY_ASC]: (modelsGroups) => sortModelsGroupsByComplexity(modelsGroups, 'ASC'),
    [ModelsSortingOptions.COMPLEXITY_DESC]: (modelsGroups) => sortModelsGroupsByComplexity(modelsGroups, 'DESC'),
    [ModelsSortingOptions.CREATION_TIME_ASC]: (modelsGroups) => sortModelsGroupsByCreationTime(modelsGroups, 'ASC'),
    [ModelsSortingOptions.CREATION_TIME_DESC]: (modelsGroups) => sortModelsGroupsByCreationTime(modelsGroups, 'DESC'),
    [ModelsSortingOptions.SIZE_ASC]: (modelsGroups) => sortModelsGroupsByModelSize(modelsGroups, 'ASC'),
    [ModelsSortingOptions.SIZE_DESC]: (modelsGroups) => sortModelsGroupsByModelSize(modelsGroups, 'DESC'),
    [ModelsSortingOptions.ACTIVE_MODEL_ASC]: (modelsGroups) => sortModelsGroupsByActiveModel(modelsGroups, 'ASC'),
    [ModelsSortingOptions.ACTIVE_MODEL_DESC]: (modelsGroups) => sortModelsGroupsByActiveModel(modelsGroups, 'DESC'),
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
