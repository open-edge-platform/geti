// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { Divider, Flex, View } from '@adobe/react-spectrum';

import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { Breadcrumbs } from '../breadcrumbs/breadcrumbs.component';
import { BreadcrumbsProps } from '../breadcrumbs/breadcrumbs.interface';
import { TutorialCardBuilder } from '../tutorial-card/tutorial-card-builder.component';

import classes from './page-layout.module.scss';

interface PageLayoutProps extends BreadcrumbsProps {
    children: JSX.Element;
    header?: ReactNode;
    tutorialCardKey?: TUTORIAL_CARD_KEYS;
}

export const PageLayout = ({ children, breadcrumbs, header, tutorialCardKey }: PageLayoutProps): JSX.Element => {
    return (
        <Flex id={`page-layout-id`} direction='column' height='100%'>
            {tutorialCardKey && (
                <TutorialCardBuilder
                    cardKey={tutorialCardKey}
                    styles={{ marginTop: 'var(--spectrum-global-dimension-size-350)' }}
                />
            )}
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <View marginY={'size-250'}>
                    <Breadcrumbs breadcrumbs={breadcrumbs} />
                </View>
                <View>{header}</View>
            </Flex>
            <Divider size='S' marginBottom={'size-250'} />

            <main className={classes.pageLayoutMain}>{children}</main>
        </Flex>
    );
};
