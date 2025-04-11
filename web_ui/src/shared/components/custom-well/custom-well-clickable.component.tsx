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

import { usePress } from 'react-aria';

import { CustomWell, CustomWellProps } from './custom-well.component';

interface CustomWellClickableProps extends CustomWellProps {
    onPress: () => void;
    onAuxClick?: () => void;
}

export const CustomWellClickable = ({
    children,
    onPress,
    flex,
    onAuxClick,
    ...props
}: CustomWellClickableProps): JSX.Element => {
    const { pressProps } = usePress({
        onPress,
    });

    return (
        <div {...pressProps} style={{ flex }} onAuxClick={onAuxClick}>
            <CustomWell {...props}>{children}</CustomWell>
        </div>
    );
};
