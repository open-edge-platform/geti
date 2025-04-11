// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC, ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';

import { BreadcrumbItemProps } from '../../../../shared/components/breadcrumbs/breadcrumb/breadcrumb.interface';
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
