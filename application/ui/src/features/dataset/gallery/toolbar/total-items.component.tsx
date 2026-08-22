// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Divider, Flex, Text } from '@geti-ui/ui';
import { useDatasetMediaWithReviewStatus } from 'hooks/use-dataset-media-with-review-status.hook';
import { useTranslation } from 'react-i18next';

type TotalItemsProps = {
    totalSelectedElements: number;
};

export const TotalItems = ({ totalSelectedElements }: TotalItemsProps) => {
    const { totalCount } = useDatasetMediaWithReviewStatus();
    const { t } = useTranslation();

    if (totalCount === 0) {
        return null;
    }

    const hasSelectedElements = totalSelectedElements > 0;

    return (
        <Flex gap={'size-100'}>
            {hasSelectedElements && (
                <>
                    <Text>{t('dataset.selectedCount', { count: totalSelectedElements })}</Text>
                    <Divider orientation={'vertical'} size={'S'} />
                </>
            )}

            <Text>{t('dataset.totalCount', { count: totalCount })}</Text>
        </Flex>
    );
};
