// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { PerformanceCategory } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { Tag } from '../../../../../../shared/components/tag/tag.component';
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
            text={`Recommended for ${performanceCategory}`}
            id={`recommended-model-for-${performanceCategory}-${idMatchingFormat(id)}-id`}
            data-testid={`recommended-model-for-${performanceCategory}-${idMatchingFormat(id)}-id`}
            className={classes.recommendedModelTag}
        />
    );
};
