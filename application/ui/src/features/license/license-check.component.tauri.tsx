// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { $api } from '@/api';
import { Loading } from '@geti-ui/ui';

import { ServerErrorFallback } from '../../routes/root/server-error-fallback.component';
import { License } from './license.component';

const REFETCH_INTERVAL = 5000;

export const LicenseCheck = ({ children }: { children: ReactNode }) => {
    const { data, isPending, isError } = $api.useQuery('get', '/api/system/info', undefined, {
        retry: 2,
        refetchInterval: (query) => {
            return query.state.data?.license_accepted ? false : REFETCH_INTERVAL;
        },
    });

    if (isPending) {
        return <Loading variant={'intel'} />;
    }

    if (isError) {
        return <ServerErrorFallback />;
    }

    if (data && !data.license_accepted && data.platform === 'windows') {
        return <License />;
    }

    return children;
};
