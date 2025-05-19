// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tag } from '@geti/ui';
import { dimensionValue } from '@react-spectrum/utils';

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
