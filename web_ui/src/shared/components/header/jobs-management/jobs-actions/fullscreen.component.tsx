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

import { Dispatch, SetStateAction } from 'react';

import { Collapse, Expand } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';

interface FullscreenProps {
    enabled: boolean;
    toggle: Dispatch<SetStateAction<boolean>>;
}

export const Fullscreen = ({ enabled, toggle }: FullscreenProps): JSX.Element => {
    return (
        <QuietActionButton
            justifySelf='end'
            id='job-scheduler-action-expand'
            data-testid='job-scheduler-action-expand'
            aria-label='Job scheduler action expand'
            onPress={() => toggle((prevState: boolean) => !prevState)}
        >
            {!enabled ? <Expand /> : <Collapse />}
        </QuietActionButton>
    );
};
