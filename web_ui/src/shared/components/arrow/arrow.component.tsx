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

import { Text } from '@adobe/react-spectrum';

interface ArrowProps {
    isHidden?: boolean;
}

export const Arrow = ({ isHidden }: ArrowProps): JSX.Element => {
    if (isHidden) return <></>;
    return <Text marginX={'size-25'}>&#8594;</Text>;
};
