// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
