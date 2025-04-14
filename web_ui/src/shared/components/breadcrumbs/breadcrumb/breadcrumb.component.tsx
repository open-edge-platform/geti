// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { Link } from 'react-router-dom';

import { BreadcrumbProps } from './breadcrumb.interface';

import classes from './breadcrumb.module.scss';

export const Breadcrumb = ({ breadcrumb, href, currentPage, id }: BreadcrumbProps): JSX.Element => {
    return currentPage ? (
        <div className={classes['spectrum-Breadcrumbs-item']} id={id}>
            <div className={classes['spectrum-Breadcrumbs-itemLink']} aria-current='page'>
                {breadcrumb}
            </div>
        </div>
    ) : (
        <div className={classes['spectrum-Breadcrumbs-item']} id={id}>
            <Link to={href ?? '/'} className={classes['spectrum-Breadcrumbs-itemLink']} tabIndex={0} viewTransition>
                {breadcrumb}
            </Link>
            <View UNSAFE_className={classes.breadcrumbDivider}>/</View>
        </div>
    );
};
