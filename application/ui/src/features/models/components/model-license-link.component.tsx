// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { License } from '@/api/types';

import { Link } from '../../../platform/components/link.component';

type ModelLicenseLinkProps = {
    license: License;
};

export const ModelLicenseLink = ({ license }: ModelLicenseLinkProps) => {
    // Some architectures (e.g. the TIMM placeholder card) have no single license document to link to
    if (license.url === '') {
        return license.name;
    }

    return (
        <Link href={license.url} target={'_blank'} rel={'noopener noreferrer'}>
            {license.name}
        </Link>
    );
};
