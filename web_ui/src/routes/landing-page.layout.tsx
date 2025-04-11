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

import { Suspense } from 'react';

import { Grid, View } from '@adobe/react-spectrum';
import { Outlet } from 'react-router-dom';

import { LandingPageSidebar } from '../pages/landing-page/landing-page-sidebar/landing-page-sidebar.component';
import { LandingPageHeader as Header } from '../shared/components/header/header.component';
import { Loading } from '../shared/components/loading/loading.component';
import { MaintenanceBanner } from '../shared/components/maintenance-banner/maintenance-banner.component';

import classes from './routes.module.scss';

export const LandingPageLayout = (): JSX.Element => {
    return (
        <Grid
            height={'100vh'}
            maxHeight={'100vh'}
            areas={['header header', 'banner banner', 'sidebar content']}
            columns={{ L: ['size-3400', 'auto'], base: ['size-600', 'auto'] }}
            rows={['size-800', 'min-content', 'auto']}
        >
            <View gridArea={'header'} zIndex={1}>
                <Header isDarkMode={false} isProject={false} />
            </View>

            <View gridArea={'banner'}>
                <MaintenanceBanner />
            </View>

            <View backgroundColor='gray-75' gridArea={'sidebar'}>
                <LandingPageSidebar />
            </View>
            <View
                maxHeight={'100%'}
                height={'100%'}
                position={'relative'}
                gridArea={'content'}
                overflow={'hidden'}
                backgroundColor={'gray-50'}
                left={'50%'}
                UNSAFE_className={classes.innerContent}
                paddingX={{ L: 'size-800', base: 'size-400' }}
                paddingY={{ L: 'size-450', base: 'size-300' }}
            >
                <Suspense fallback={<Loading size='L' />}>
                    <Outlet />
                </Suspense>
            </View>
        </Grid>
    );
};
