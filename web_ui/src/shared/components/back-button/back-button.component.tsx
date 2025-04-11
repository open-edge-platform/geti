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

import { Back } from '../../../assets/icons';
import { ActionButton } from '../button/button.component';

interface BackButtonProps {
    onPress: () => void;
}

export const BackButton = ({ onPress }: BackButtonProps): JSX.Element => {
    return (
        <ActionButton id='go-back-button' data-testid='go-back-button' isQuiet onPress={onPress} aria-label='Back'>
            <Back />
        </ActionButton>
    );
};
