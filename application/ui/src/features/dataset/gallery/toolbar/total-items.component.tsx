// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Text } from '@geti-ui/ui';
import { useDatasetMediaWithReviewStatus } from 'hooks/use-dataset-media-with-review-status.hook';

type TotalItemsProps = {
    totalSelectedElements: number;
};

const pluralRules = new Intl.PluralRules('en');

export const TotalItems = ({ totalSelectedElements }: TotalItemsProps) => {
    const { totalCount } = useDatasetMediaWithReviewStatus();

    if (totalCount === 0) {
        return null;
    }

    const hasSelectedElements = totalSelectedElements > 0;

    if (hasSelectedElements) {
        return <Text>{`${totalSelectedElements}/${totalCount} selected`}</Text>;
    }

    return <Text>{`${totalCount} media ${pluralRules.select(totalCount) === 'one' ? 'item' : 'items'}`}</Text>;
};
