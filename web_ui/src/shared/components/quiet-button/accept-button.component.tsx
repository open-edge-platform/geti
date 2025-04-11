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

import { SpectrumActionButtonProps } from '@react-types/button';

import { Accept } from '../../../assets/icons';
import { ActionButton } from '../button/button.component';

import sharedClasses from '../../shared.module.scss';

export const AcceptButton = (props: SpectrumActionButtonProps) => {
    return (
        <ActionButton
            isQuiet
            {...props}
            UNSAFE_className={`${sharedClasses.acceptButton} ${props.UNSAFE_className ?? ''}`}
        >
            <Accept />
        </ActionButton>
    );
};
