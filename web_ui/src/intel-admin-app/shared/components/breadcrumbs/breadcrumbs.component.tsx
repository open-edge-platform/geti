// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Breadcrumbs as BreadcrumbsComponent, Flex, type BreadcrumbsProps } from '@geti/ui';

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
