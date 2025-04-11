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
