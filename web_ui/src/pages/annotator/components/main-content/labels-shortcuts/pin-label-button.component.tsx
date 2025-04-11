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

import { Pin } from '../../../../../assets/icons';
import { ActionButton } from '../../../../../shared/components/button/button.component';

interface PinLabelButtonProps {
    pinLabel: (labelId: string) => void;
    labelId: string;
}

export const PinLabelButton = ({ pinLabel, labelId }: PinLabelButtonProps): JSX.Element => {
    return (
        <ActionButton isQuiet onPress={() => pinLabel(labelId)} width='size-225' height='size-225'>
            <Pin aria-label={`${labelId}-pin-icon`} id={'pin-icon'} />
        </ActionButton>
    );
};
