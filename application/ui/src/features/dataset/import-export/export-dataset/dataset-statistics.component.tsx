// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DatasetStatistics } from '@/components/dataset-statistics/dataset-statistics.component';

import { useGetDatasetItems } from '../../../../hooks/use-get-dataset-items.hook';

export const MainDatasetStatistics = ({ datasetViewId }: { datasetViewId?: string }) => {
    const { totalCount: totalMediaItems } = useGetDatasetItems({ datasetViewId });
    const { totalCount: totalAnnotatedItems } = useGetDatasetItems({
        annotationStatus: 'with_annotations',
        datasetViewId,
    });

    return (
        <DatasetStatistics label='items' totalMediaItems={totalMediaItems} totalAnnotatedItems={totalAnnotatedItems} />
    );
};
