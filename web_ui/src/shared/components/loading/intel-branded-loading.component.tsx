// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import IntelBrandedLoadingGif from '../../../assets/images/intel-loading.webp';

export const IntelBrandedLoading = (): JSX.Element => {
    return (
        <Flex justifyContent='center' alignItems='center' height='100vh' direction='column'>
            <img
                src={IntelBrandedLoadingGif}
                // eslint-disable-next-line jsx-a11y/no-noninteractive-element-to-interactive-role
                role='progressbar'
                alt='Loading'
                width={dimensionValue('size-2400')}
                height={dimensionValue('size-2400')}
            />
        </Flex>
    );
};
