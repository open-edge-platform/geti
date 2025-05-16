// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@adobe/react-spectrum';
import { Tag } from '@geti/ui';

import {
    LabelTreeGroupProps,
    TreeItemPresentationModeProps,
} from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
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
