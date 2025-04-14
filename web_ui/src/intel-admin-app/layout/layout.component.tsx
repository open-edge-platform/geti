// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
