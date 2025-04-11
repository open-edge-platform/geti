// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
