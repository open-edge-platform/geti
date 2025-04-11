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
import { View } from '@react-spectrum/view';
import isEmpty from 'lodash/isEmpty';

import {
    LabelTreeLabelProps,
    TreeItemPresentationModeProps,
} from '../../../../../core/labels/label-tree-view.interface';
import { getLabelId } from '../../../../../core/labels/utils';
import { LabelColorThumb } from '../../../label-color-thumb/label-color-thumb.component';
import { TruncatedTextWithTooltip } from '../../../truncated-text/truncated-text.component';
import { HotkeyLabel } from './hotkey-name-field/hotkey-label.component';

const attrs = {
    itemLabel: { classes: 'spectrum-TreeView-itemLabel' },
};

export const LabelPresentationMode = ({
    item: label,
}: TreeItemPresentationModeProps<LabelTreeLabelProps>): JSX.Element => {
    const { name, hotkey } = label;

    return (
        <Flex
            alignItems='center'
            gap='size-100'
            width={'100%'}
            marginStart={isEmpty(label.children) ? 'size-100' : undefined}
        >
            <LabelColorThumb
                label={label}
                id={`color-${getLabelId('tree', label)}`}
                data-testid={`color-${getLabelId('tree', label)}`}
            />
            <Flex alignItems={'center'} justifyContent={'space-between'} minWidth={0} width={'100%'} gap={'size-100'}>
                <Flex gap={'size-100'} alignItems={'center'}>
                    <TruncatedTextWithTooltip
                        id={`name-${getLabelId('tree', label)}`}
                        data-testid={`${label.id}-label-${label.name}`}
                        {...attrs.itemLabel}
                    >
                        {name}
                    </TruncatedTextWithTooltip>
                </Flex>

                <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-600'}>
                    {hotkey ? (
                        <Flex
                            gap={'size-100'}
                            alignItems={'center'}
                            width={'size-1700'}
                            UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-50)' }}
                        >
                            <HotkeyLabel />
                            <View
                                backgroundColor={'gray-200'}
                                borderRadius={'large'}
                                width={'size-900'}
                                UNSAFE_style={{ textAlign: 'center' }}
                                padding={'size-25s'}
                            >
                                <Text id={`label-hotkey-${name}`}>{hotkey.toUpperCase()}</Text>
                            </View>
                        </Flex>
                    ) : (
                        <></>
                    )}
                </Flex>
            </Flex>
        </Flex>
    );
};
