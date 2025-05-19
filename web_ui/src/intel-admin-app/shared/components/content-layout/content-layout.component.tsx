// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';
import { BreadcrumbItemProps } from '@geti/ui';

import { Breadcrumbs } from '../breadcrumbs/breadcrumbs.component';

import classes from './content-layout.module.scss';

interface ContentLayoutProps {
    breadcrumbs: BreadcrumbItemProps[];
    children: ReactNode;
}

export const ContentLayout: FC<ContentLayoutProps> = ({ breadcrumbs, children }) => {
    return (
        <>
            <Breadcrumbs breadcrumbs={breadcrumbs} />
            <View
                overflow={'hidden scroll'}
                paddingX={{ base: 'size-200', L: 'size-1000' }}
                paddingY={{ base: 'size-200', L: 'size-250' }}
            >
                <View
                    padding={'size-400'}
                    paddingTop={'size-200'}
                    UNSAFE_className={classes.contentLayoutContainer}
                    height={'100%'}
                >
                    <View overflow={'auto scroll'} height={'100%'}>
                        {children}
                    </View>
                </View>
            </View>
        </>
    );
};
