// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Key, useMemo } from 'react';

import { ActionButton, Flex, Grid, Item, Menu, MenuTrigger, Picker } from '@geti-ui/ui';
import { MoreMenu } from '@geti-ui/ui/icons';
import { useProjectTask } from 'hooks/use-project-task.hook';
import { useTranslation } from 'react-i18next';

import { TrainModel } from '../../train-model/train-model.component';
import { useModelListing } from '../provider/model-listing-provider';
import type { GroupByMode, SortBy } from '../types';
import { ExpandableSearch } from './expandable-search/expandable-search.component';
import { getPerformanceColumnLabel } from './model-row/utils';

type MoreOptionsProps = {
    showFailedModels: boolean;
    onToggleShowFailedModels: () => void;
};
const MoreOptions = ({ showFailedModels, onToggleShowFailedModels }: MoreOptionsProps) => {
    const { t } = useTranslation();
    const handleOptionsAction = (key: Key) => {
        switch (key) {
            case 'show-failed':
                onToggleShowFailedModels();
                break;
            default:
                break;
        }
    };

    return (
        <MenuTrigger>
            <ActionButton isQuiet aria-label={t('models.listingOptionsAriaLabel')}>
                <MoreMenu />
            </ActionButton>
            <Menu onAction={handleOptionsAction} aria-label={t('models.listingOptionsMenuAriaLabel')}>
                <Item key={'show-failed'}>
                    {showFailedModels ? t('models.hideFailedModels') : t('models.showFailedModels')}
                </Item>
            </Menu>
        </MenuTrigger>
    );
};

export const Header = () => {
    const { t } = useTranslation();
    const {
        groupBy,
        sortBy,
        onGroupByChange,
        onSortChange,
        searchBy,
        onSearchChange,
        showFailedModels,
        onToggleShowFailedModels,
        groupedModels,
    } = useModelListing();
    const taskType = useProjectTask();
    const performanceMetricName = useMemo(() => {
        const models = groupedModels.flatMap((group) => group.models);

        return getPerformanceColumnLabel(models, taskType);
    }, [groupedModels, taskType]);

    return (
        <Grid columns={['auto auto 1fr auto']} gap={'size-100'} alignItems={'center'}>
            <Flex gap={'size-100'}>
                <Picker
                    placeholder={t('models.groupByPlaceholder')}
                    width={'size-2400'}
                    aria-label={t('models.groupModelsAriaLabel')}
                    selectedKey={groupBy}
                    onSelectionChange={(key) => onGroupByChange(key as GroupByMode)}
                >
                    <Item key='dataset'>{t('models.groupByDataset')}</Item>
                    <Item key='architecture'>{t('models.groupByArchitecture')}</Item>
                </Picker>
                <Picker
                    placeholder={t('models.sortByPlaceholder')}
                    width={'size-2000'}
                    aria-label={t('models.sortModelsAriaLabel')}
                    selectedKey={sortBy}
                    onSelectionChange={(key) => onSortChange(key as SortBy)}
                >
                    <Item key='name'>{t('models.sortName')}</Item>
                    <Item key='trained'>{t('models.sortTrained')}</Item>
                    {groupBy === 'dataset' ? (
                        <Item key='architecture'>{t('models.sortArchitecture')}</Item>
                    ) : (
                        <Item key='dataset'>{t('models.sortDataset')}</Item>
                    )}
                    <Item key='device'>{t('models.sortDevice')}</Item>
                    <Item key='size'>{t('models.sortSize')}</Item>
                    <Item key='score'>{t('models.sortByMetricTemplate', { metric: t(performanceMetricName) })}</Item>
                </Picker>
            </Flex>

            <MoreOptions showFailedModels={showFailedModels} onToggleShowFailedModels={onToggleShowFailedModels} />

            <Flex marginStart={'auto'} gap={'size-100'}>
                <ExpandableSearch value={searchBy} onChange={onSearchChange} />
                <TrainModel />
            </Flex>
        </Grid>
    );
};
