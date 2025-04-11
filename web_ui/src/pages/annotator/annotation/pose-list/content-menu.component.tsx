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

import { MoreMenu } from '../../../../assets/icons';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { MenuTrigger } from '../../../../shared/components/menu-trigger/menu-trigger.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';

interface ContentMenuProps {
    point: KeypointNode;
    onUpdate: (point: KeypointNode) => void;
}

export const OPTION_VISIBLE = 'Mark as visible';
export const OPTION_OCCLUDED = 'Mark as occluded';

export const ContentMenu = ({ point, onUpdate }: ContentMenuProps) => {
    const option = point.isVisible ? OPTION_OCCLUDED : OPTION_VISIBLE;

    return (
        <MenuTrigger
            id={`pose-point-label-${point.label.id}`}
            items={[option]}
            onAction={() => onUpdate({ ...point, isVisible: !point.isVisible })}
        >
            <QuietActionButton aria-label='menu trigger'>
                <MoreMenu />
            </QuietActionButton>
        </MenuTrigger>
    );
};
