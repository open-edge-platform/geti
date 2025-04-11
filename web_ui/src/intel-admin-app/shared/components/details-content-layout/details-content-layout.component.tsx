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

import { Grid, View } from '@adobe/react-spectrum';
import { Outlet } from 'react-router-dom';

import { BreadcrumbItemProps } from '../../../../shared/components/breadcrumbs/breadcrumb/breadcrumb.interface';
import { Breadcrumbs } from '../breadcrumbs/breadcrumbs.component';

interface DetailsContentLayoutProps {
    breadcrumbs: BreadcrumbItemProps[];
    sidebar: ReactNode;
}

export const DetailsContentLayout: FC<DetailsContentLayoutProps> = ({ breadcrumbs, sidebar }) => {
    return (
        <>
            <Breadcrumbs breadcrumbs={breadcrumbs} />
            <Grid columns={['size-3600', 'auto']} height={'100%'} UNSAFE_style={{ overflowY: 'hidden' }}>
                {sidebar}
                <View
                    backgroundColor={'gray-50'}
                    paddingX={'size-800'}
                    paddingY={'size-450'}
                    height={'100%'}
                    overflow={'hidden'}
                    UNSAFE_style={{ boxSizing: 'border-box' }}
                >
                    <Outlet />
                </View>
            </Grid>
        </>
    );
};
