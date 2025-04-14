// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

export interface BreadcrumbItemProps {
    id: string;
    breadcrumb: ReactNode;
    href?: string;
}

export interface BreadcrumbProps extends BreadcrumbItemProps {
    currentPage: boolean;
}
