// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

interface ValidationErrorMsgProps {
    errorMsg: string;
    inheritHeight?: boolean;
    maxWidth?: string;
    gridArea?: string;
}

export const ValidationErrorMsg = ({
    errorMsg,
    inheritHeight = false,
    maxWidth,
    gridArea,
}: ValidationErrorMsgProps): JSX.Element => {
    if (isEmpty(errorMsg)) {
        return <></>;
    }

    return (
        <Flex
            alignItems={'center'}
            height={inheritHeight ? 'inherit' : 'size-300'}
            UNSAFE_style={{ fontSize: 'small', color: 'var(--brand-coral-cobalt)' }}
            maxWidth={maxWidth ?? 'inherit'}
            gridArea={gridArea}
        >
            <Text UNSAFE_style={{ whiteSpace: 'normal' }} data-testid={'label-error-message-id'}>
                {errorMsg}
            </Text>
        </Flex>
    );
};
