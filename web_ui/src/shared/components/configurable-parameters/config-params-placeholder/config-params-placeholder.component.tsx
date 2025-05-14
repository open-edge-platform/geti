// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Skeleton } from '../../skeleton/skeleton.component';

export const ConfigParamsPlaceholder = (): JSX.Element => {
    return (
        <div
            style={{ display: 'flex', width: '100%', height: '100%', gap: 32 }}
            data-testid={'config-params-placeholder-id'}
        >
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
                <Skeleton UNSAFE_style={{ height: 50, width: '40%' }} />
                <Skeleton UNSAFE_style={{ height: 50, width: '40%' }} />
                <Skeleton UNSAFE_style={{ height: 50, width: '40%' }} />
            </div>
            <div
                style={{
                    width: 1,
                    background: 'var(--spectrum-global-color-gray-200)',
                    height: 400,
                    alignSelf: 'flex-start',
                }}
            />
            <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: 20 }}>
                <Skeleton UNSAFE_style={{ height: 100, width: '100%' }} />
                <Skeleton UNSAFE_style={{ height: 100, width: '100%' }} />
                <Skeleton UNSAFE_style={{ height: 100, width: '100%' }} />
            </div>
        </div>
    );
};
