// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import ContentLoader from 'react-content-loader';

export const ConfigParamsPlaceholder = (): JSX.Element => {
    return (
        <ContentLoader
            speed={2}
            width={'100%'}
            height={'100%'}
            backgroundColor='var(--spectrum-global-color-gray-75)'
            foregroundColor='var(--spectrum-global-color-gray-200)'
            data-testid={'config-params-placeholder-id'}
        >
            <rect x='20' y='10' rx={10} ry={10} width='40%' height='50' />
            <rect x='20' y='70' rx={10} ry={10} width='40%' height='50' />
            <rect x='20' y='130' rx={10} ry={10} width='40%' height='50' />

            <rect x={'45%'} y={10} width={1} height={400} />

            <rect x='48%' y='10' rx={10} ry={10} width='50%' height='100' />
            <rect x='48%' y='120' rx={10} ry={10} width='50%' height='100' />
            <rect x='48%' y='230' rx={10} ry={10} width='50%' height='100' />
        </ContentLoader>
    );
};
