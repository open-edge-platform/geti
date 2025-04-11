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

import { useMemo } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import { CloseSmall } from '../../../../../assets/icons';
import { fetchLabelsTree, findLabelParents } from '../../../../../core/labels/annotator-utils/labels-utils';
import { LabelTreeItem } from '../../../../../core/labels/label-tree-view.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { getLabelId } from '../../../../../core/labels/utils';
import { LabelTag } from '../label-tag/label-tag.component';

interface HierarchicalLabelViewProps {
    label: Label;
    isPointer: boolean;
    labels: ReadonlyArray<Label>;
    onOpenList: () => void;
    resetHandler: () => void;
    panelClickHandler?: () => void;
}

export const HierarchicalLabelView = ({
    label,
    labels,
    onOpenList,
    resetHandler,
    panelClickHandler,
    isPointer = false,
}: HierarchicalLabelViewProps): JSX.Element => {
    const labelAsTreeItem = useMemo((): LabelTreeItem => {
        return fetchLabelsTree([...findLabelParents(labels, label), label])[0];
    }, [label, labels]);

    const labelHierarchyArray = useMemo((): LabelTreeItem[] => {
        const entries: LabelTreeItem[] = [];
        let entryLabel: LabelTreeItem = labelAsTreeItem;

        while (entryLabel) {
            entries.push(entryLabel);
            entryLabel = entryLabel.children[0];
        }

        return entries;
    }, [labelAsTreeItem]);

    return (
        <div style={{ width: 'fit-content', cursor: 'default', userSelect: 'none' }} onClick={panelClickHandler}>
            <View backgroundColor='gray-50' paddingX='size-150' paddingY='size-75'>
                <Flex alignItems='center' gap='size-125'>
                    <Flex alignItems='center' gap='size-125'>
                        {labelHierarchyArray.map((current: LabelTreeItem) => (
                            <LabelTag
                                key={current.id}
                                onClick={onOpenList}
                                isPointer={isPointer}
                                label={current as Label}
                                id={getLabelId('default', current as Label)}
                            />
                        ))}
                    </Flex>
                    <span
                        style={{ cursor: 'pointer', lineHeight: 0 }}
                        onClick={resetHandler}
                        aria-label='Close hierarchical label view'
                    >
                        <CloseSmall />
                    </span>
                </Flex>
            </View>
        </div>
    );
};
