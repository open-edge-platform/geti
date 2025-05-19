// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';

import { Breadcrumbs as BreadcrumbsComponent } from '../../../../../packages/ui/src/breadcrumbs/breadcrumbs.component';
import { BreadcrumbsProps } from '../../../../../packages/ui/src/breadcrumbs/breadcrumbs.interface';
import IntelAdminBackground from '../../../../assets/images/intel-admin-app-background.webp';

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
