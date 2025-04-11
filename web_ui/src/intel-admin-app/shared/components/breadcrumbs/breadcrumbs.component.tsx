// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';

import IntelAdminBackground from '../../../../assets/images/intel-admin-app-background.webp';
import { Breadcrumbs as BreadcrumbsComponent } from '../../../../shared/components/breadcrumbs/breadcrumbs.component';
import { BreadcrumbsProps } from '../../../../shared/components/breadcrumbs/breadcrumbs.interface';

import classes from './breadcrumbs.module.scss';

export const Breadcrumbs = ({ breadcrumbs }: BreadcrumbsProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} UNSAFE_className={classes.breadcrumbsContainer}>
            <img
                src={IntelAdminBackground}
                alt={'Intel admin app background'}
                className={classes.intelAdminBackground}
            />
            <BreadcrumbsComponent breadcrumbs={breadcrumbs} />
        </Flex>
    );
};
