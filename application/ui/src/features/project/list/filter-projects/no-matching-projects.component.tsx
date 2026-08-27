// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, Heading, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { ReactComponent as EmptyFolderImage } from '../../../../assets/empty-folder.svg';

import classes from './no-matching-projects.module.scss';

export const NoMatchingProjects = () => {
    const { t } = useTranslation();

    return (
        <Flex
            gap={'size-100'}
            direction={'column'}
            alignItems={'center'}
            justifyContent={'center'}
            UNSAFE_className={classes.container}
        >
            <EmptyFolderImage aria-label={'no matching projects'} />

            <Heading level={3} margin={0}>
                {t('projectList.noMatching.title')}
            </Heading>

            <Text UNSAFE_style={{ textAlign: 'center' }}>{t('projectList.noMatching.hint')}</Text>
        </Flex>
    );
};
