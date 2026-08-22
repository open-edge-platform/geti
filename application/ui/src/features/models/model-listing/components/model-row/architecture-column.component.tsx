// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ModelArchitectureWithPerformanceCategory } from '@/api/types';
import { Flex, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { PerformanceCategoryBadge } from './performance-category-badge.component';

import classes from './model-row.module.scss';

type ArchitectureColumnProps = {
    architecture: ModelArchitectureWithPerformanceCategory | undefined;
};

export const ArchitectureColumn = ({ architecture }: ArchitectureColumnProps) => {
    const { t } = useTranslation();

    // Should never happen, but just in case
    if (architecture === undefined) {
        return <Text>{t('models.unknownArchitecture')}</Text>;
    }

    return (
        <Flex direction={'column'} gap={'size-100'}>
            <Text UNSAFE_className={classes.smallText}>
                {architecture.name} ({architecture.license})
            </Text>
            {architecture.performanceCategory !== undefined && (
                <PerformanceCategoryBadge
                    id={'architecture-name'}
                    performanceCategory={architecture.performanceCategory}
                />
            )}
        </Flex>
    );
};
