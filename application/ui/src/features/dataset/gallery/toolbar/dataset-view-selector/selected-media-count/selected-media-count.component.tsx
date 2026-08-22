// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { pluralizeItems } from '../../../../../../shared/util';

import classes from './selected-media-count.module.scss';

type SelectedMediaCountProps = {
    count: number;
};

export const SelectedMediaCount = ({ count }: SelectedMediaCountProps) => {
    const { t } = useTranslation();

    return (
        <Flex direction={'column'} gap={'size-100'}>
            <Text UNSAFE_className={classes.selectedMedia}>{t('dataset.selectedMediaLabel')}</Text>
            <Text UNSAFE_className={classes.selectedMediaCount}>{`${count} ${pluralizeItems(count)}`}</Text>
        </Flex>
    );
};
