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

import {
    LabelTreeGroupProps,
    TreeItemPresentationModeProps,
} from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { Tag } from '../../../tag/tag.component';
import { ItemEditionState } from '../item-edition-state/item-edition-state.component';

import classes from './label-presentation-mode.module.scss';

export const GroupPresentationMode = ({
    item: group,
    newTree,
}: TreeItemPresentationModeProps<LabelTreeGroupProps>): JSX.Element => {
    const { name, relation, state } = group;
    const DOT_SIGN = '∙';
    const prefix = relation === LabelsRelationType.SINGLE_SELECTION ? DOT_SIGN : `${DOT_SIGN}${DOT_SIGN}`;

    return (
        <Flex gap={'size-600'} width={'100%'} alignItems={'center'}>
            <Flex
                gap={'size-100'}
                width={'100%'}
                justifyContent={'space-between'}
                alignItems={'center'}
                height={'100%'}
            >
                <Flex gap={'size-100'}>
                    <Text UNSAFE_style={{ wordBreak: 'break-all' }}>{name}</Text>
                    {!newTree && <ItemEditionState state={state} idSuffix={idMatchingFormat(name)} />}
                </Flex>
                <Tag
                    className={classes.tag}
                    withDot={false}
                    prefix={<>{prefix}</>}
                    text={`${relation}`}
                    tooltip={
                        relation === LabelsRelationType.MULTI_SELECTION
                            ? 'Multiple labels from such group can be applied to an image/frame.'
                            : 'Only one label from such group can be applied to an image/frame.'
                    }
                />
            </Flex>
        </Flex>
    );
};
