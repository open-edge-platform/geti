// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
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

import { Tag } from '../../../../shared/components/tag/tag.component';

export const VisualPromptModelBetaWarning = () => {
    return (
        <Flex
            maxWidth={'67rem'}
            alignItems={'center'}
            UNSAFE_style={{
                border: '1px solid var(--energy-blue)',
                padding: dimensionValue('size-100'),
            }}
            gap={'size-100'}
        >
            <Tag text='Beta' />
            <Flex wrap={'wrap'}>Using prompt learning models for inference is currently an experimental feature</Flex>
        </Flex>
    );
};
