// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import classes from './menu-item-image.module.scss';

export const MenuItemImage = ({ children }: { children: ReactElement }): JSX.Element => {
    return (
        <svg viewBox={'0 0 36 36'} role={'img'} className={classes.icon}>
            {children}
        </svg>
    );
};
