// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Grid } from '@adobe/react-spectrum';
import { Outlet } from 'react-router-dom';

import { Header } from './header.component';

import classes from './layout.module.scss';

export const Layout = (): JSX.Element => {
    return (
        <Grid
            rows={{ base: ['size-1000', 'size-550', 'auto'], L: ['size-1000', 'size-700', 'auto'] }}
            height={'100vh'}
            rowGap={'size-10'}
            UNSAFE_className={classes.layoutContainer}
        >
            <Header />
            <Outlet />
        </Grid>
    );
};
