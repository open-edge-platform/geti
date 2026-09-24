// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetRevision, DatasetSubset, Model } from '@/api/types';
import { GalleryViewModeMenu } from '@/components/gallery-view-mode-menu/gallery-view-mode-menu.component';
import { useTranslation } from '@/i18n';
import { Flex, Text, ViewModes } from '@geti-ui/ui';
import { useNumberFormatter } from 'react-aria';

import { useGetDatasetRevisionItems } from '../../../../hooks/use-get-dataset-revision-items.hook';
import { useViewMode } from '../../../../hooks/use-view-mode.hook';
import { type GalleryViewMode } from '../../../../shared/gallery-view-modes';
import { getAllModelsWithOpenVINOVariants, type SelectableModel } from '../../../../shared/selectable-model';
import { Box } from '../components/box/box.component';
import { SubsetGallery } from './subset-gallery.component';

type SubsetBoxProps = {
    title: string;
    subset: DatasetSubset;
    datasetRevisionId: string;
    totalItems: number;
    selectedModel: SelectableModel | undefined;
};

const SubsetBox = ({ title, subset, datasetRevisionId, totalItems, selectedModel }: SubsetBoxProps) => {
    const { items, fetchNextPage, hasNextPage, isFetchingNextPage, isPending, totalCount } = useGetDatasetRevisionItems(
        {
            datasetRevisionId,
            subsets: [subset],
        }
    );
    const [viewMode, setViewMode] = useViewMode(`model-training-datasets-${subset}-view-mode`, ViewModes.MEDIUM);

    const formatter = useNumberFormatter({ style: 'percent', maximumFractionDigits: 0 });
    const subsetPercentage = totalItems > 0 ? totalCount / totalItems : 0;

    return (
        <Box
            title={`${title} ${formatter.format(subsetPercentage)} (${totalCount})`}
            actions={<GalleryViewModeMenu viewMode={viewMode} setViewMode={setViewMode} />}
            content={
                <SubsetGallery
                    items={items}
                    datasetRevisionId={datasetRevisionId}
                    viewMode={viewMode as GalleryViewMode}
                    fetchNextPage={fetchNextPage}
                    hasNextPage={hasNextPage}
                    isFetchingNextPage={isFetchingNextPage}
                    isPending={isPending}
                    selectedModel={selectedModel}
                />
            }
        />
    );
};

const ModelTrainingContent = ({ datasetRevision, model }: { datasetRevision: DatasetRevision; model: Model }) => {
    const { t } = useTranslation();
    const totalItems = datasetRevision.item_counts?.total ?? 0;
    const datasetRevisionId = String(datasetRevision.id);

    // Predictions can only be run with an OpenVINO variant of the model being inspected
    const selectedModel = getAllModelsWithOpenVINOVariants([model]).at(0);

    return (
        <Flex gap={'size-300'} width={'100%'}>
            <SubsetBox
                title={t('common.labels.training')}
                subset={'training'}
                datasetRevisionId={datasetRevisionId}
                totalItems={totalItems}
                selectedModel={selectedModel}
            />
            <SubsetBox
                title={t('common.labels.validation')}
                subset={'validation'}
                datasetRevisionId={datasetRevisionId}
                totalItems={totalItems}
                selectedModel={selectedModel}
            />
            <SubsetBox
                title={t('common.labels.testing')}
                subset={'testing'}
                datasetRevisionId={datasetRevisionId}
                totalItems={totalItems}
                selectedModel={selectedModel}
            />
        </Flex>
    );
};

export const ModelTrainingDatasets = ({
    datasetRevision,
    model,
}: {
    datasetRevision?: DatasetRevision;
    model: Model;
}) => {
    const { t } = useTranslation();

    if (!datasetRevision || !datasetRevision.id) {
        return (
            <Flex justifyContent={'center'} alignItems={'center'} height={'size-3000'}>
                <Text>{t('dataset.revisions.notFoundForModel')}</Text>
            </Flex>
        );
    }

    if (datasetRevision.files_deleted) {
        return (
            <Flex justifyContent={'center'} alignItems={'center'} height={'size-3000'}>
                <Text>{t('dataset.revisions.filesDeleted')}</Text>
            </Flex>
        );
    }

    return <ModelTrainingContent datasetRevision={datasetRevision} model={model} />;
};
