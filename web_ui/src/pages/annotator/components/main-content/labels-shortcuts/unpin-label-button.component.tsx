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

import { Unpin } from '../../../../../assets/icons';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { useRenderDelay } from '../../../../../shared/hooks/use-render-delay.hook';

interface UnpinLabelButtonProps {
    unPinLabel: (labelId: string) => void;
    labelId: string;
    delay?: number;
    shift?: boolean;
}

export const UnpinLabelButton = ({ unPinLabel, labelId, delay = 0, shift = false }: UnpinLabelButtonProps) => {
    //NOTE: unpin should be shift by button right margin value
    const MARGIN = shift ? -12 : 0;
    const isShown = useRenderDelay(delay);

    return isShown ? (
        <ActionButton isQuiet onPress={() => unPinLabel(labelId)} marginEnd={MARGIN} width='size-225' height='size-225'>
            <Unpin aria-label={`${labelId}-unpin-icon`} id={'unpin-icon'} />
        </ActionButton>
    ) : (
        <></>
    );
};
