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

import { View } from '@react-spectrum/view';

import { ChevronDownSmallLight, ChevronRightSmallLight } from '../../../../assets/icons';
import { ActionButton } from '../../button/button.component';

interface LabelTreeViewItemPrefixProps {
    isOpen: boolean;
    onOpenClickHandler: () => void;
    childrenLength: number;
}

export const LabelTreeViewItemPrefix = ({
    isOpen,
    onOpenClickHandler,
    childrenLength,
}: LabelTreeViewItemPrefixProps): JSX.Element => {
    return childrenLength > 0 ? (
        <ActionButton id='toggle-label-item' data-testid='toggle-label-item' isQuiet onPress={onOpenClickHandler}>
            {isOpen ? <ChevronDownSmallLight /> : <ChevronRightSmallLight />}
        </ActionButton>
    ) : (
        <View width={'16px'} height={'16px'} />
    );
};
