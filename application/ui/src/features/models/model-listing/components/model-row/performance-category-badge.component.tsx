// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Text } from '@geti-ui/ui';
import { capitalize } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { ReactComponent as ThumbsUp } from '../../../../../assets/icons/thumbs-up.svg';
import { ModelBadge } from './model-badge.component';

type PerformanceCategoryBadgeProps = {
    performanceCategory: string;
    id?: string;
    color?: string;
};

const CATEGORY_KEYS: Record<string, string> = {
    speed: 'models.performanceSpeed',
    accuracy: 'models.performanceAccuracy',
    balance: 'models.performanceBalance',
};

export const PerformanceCategoryBadge = ({ performanceCategory, id, color }: PerformanceCategoryBadgeProps) => {
    const { t } = useTranslation();
    const key = CATEGORY_KEYS[performanceCategory] ?? performanceCategory;

    return (
        <ModelBadge id={id} color={color}>
            <ThumbsUp />
            <Text>{t(key, { defaultValue: capitalize(performanceCategory) })}</Text>
        </ModelBadge>
    );
};
