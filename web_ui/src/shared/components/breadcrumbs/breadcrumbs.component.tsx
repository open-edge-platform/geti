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

import { Breadcrumb } from './breadcrumb/breadcrumb.component';
import { BreadcrumbItemProps } from './breadcrumb/breadcrumb.interface';
import { BreadcrumbsProps } from './breadcrumbs.interface';

export const Breadcrumbs = ({ breadcrumbs }: BreadcrumbsProps): JSX.Element => {
    return (
        <nav aria-label='Breadcrumbs'>
            {breadcrumbs.map(({ id, breadcrumb, href }: BreadcrumbItemProps, index: number) => (
                <Breadcrumb
                    key={id}
                    id={id}
                    currentPage={index === breadcrumbs?.length - 1}
                    breadcrumb={breadcrumb}
                    href={href}
                />
            ))}
        </nav>
    );
};
