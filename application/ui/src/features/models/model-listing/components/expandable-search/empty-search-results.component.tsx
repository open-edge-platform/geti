// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, Heading } from '@geti-ui/ui';
import { Search } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

export const EmptySearchResults = () => {
    const { t } = useTranslation();

    return (
        <Flex direction={'column'} alignItems={'center'} justifyContent={'center'} gap={'size-200'} height={'100%'}>
            <Search />
            <Heading level={3}>{t('models.noModelsFound')}</Heading>
        </Flex>
    );
};
