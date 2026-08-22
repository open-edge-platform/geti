// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { FilterByStatusKey } from '@/api/types';
import { DimensionValue, Item, Picker } from '@geti-ui/ui';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { useTranslation } from 'react-i18next';

const FILTER_BY_STATUS_OPTIONS: { nameKey: string; key: FilterByStatusKey }[] = [
    { nameKey: 'dataset.statusAll', key: 'all' },
    { nameKey: 'dataset.statusWithAnnotations', key: 'with_annotations' },
    { nameKey: 'dataset.statusMissingAnnotations', key: 'missing_annotations' },
];

type FilterByStatusProps = {
    width?: DimensionValue;
};

export const FilterByStatus = ({ width }: FilterByStatusProps) => {
    const { annotationStatus, setAnnotationStatus } = useDatasetFiltersSearchParams();
    const { t } = useTranslation();

    return (
        <Picker
            width={width}
            aria-label={t('dataset.mediaStatusAriaLabel')}
            items={FILTER_BY_STATUS_OPTIONS}
            selectedKey={annotationStatus ?? FILTER_BY_STATUS_OPTIONS[0].key}
            onSelectionChange={(status) => setAnnotationStatus(status as FilterByStatusKey)}
        >
            {(item) => <Item>{t(item.nameKey)}</Item>}
        </Picker>
    );
};
