// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tag } from '@geti/ui';
import { capitalize } from 'lodash-es';

import { PerformanceCategory } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './model-card.module.scss';

interface RecommendedModelTagProps {
    id: string;
    performanceCategory: PerformanceCategory;
}

export const RecommendedModelTag = ({ id, performanceCategory }: RecommendedModelTagProps): JSX.Element => {
    return (
        <Tag
            withDot={false}
            text={`Recommended for ${capitalize(performanceCategory)}`}
            id={`recommended-model-for-${performanceCategory}-${idMatchingFormat(id)}-id`}
            data-testid={`recommended-model-for-${performanceCategory}-${idMatchingFormat(id)}-id`}
            className={classes.recommendedModelTag}
        />
    );
};
