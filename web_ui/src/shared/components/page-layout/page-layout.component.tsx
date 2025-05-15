// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Divider, Flex, View } from '@adobe/react-spectrum';
import { Breadcrumbs, BreadcrumbsProps } from '@geti/ui';

import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
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
