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

import { Flex } from '@adobe/react-spectrum';

import { LabelTreeLabelProps } from '../../../../core/labels/label-tree-view.interface';
import { LabelEditionMode } from './label-edition-mode/label-edition-mode.component';
import { LabelPresentationMode } from './label-presentation-mode/label-presentation-mode.component';
import { LabelTreeViewItemPrefix } from './label-tree-view-item-prefix.component';
import { TreeViewItemContentProps, TreeViewItemEditModeProps } from './label-tree-view-item.interface';

type LabelTreeViewLabelProps = TreeViewItemEditModeProps<LabelTreeLabelProps> & TreeViewItemContentProps;

export const LabelTreeViewLabel = ({
    item,
    savedItem,
    save,
    flatListProjectItems: flatProjectLabels,
    newTree,
    onOpenClickHandler,
    isOpen,
    inEditionMode,
    domains,
    setValidationError,
    validationErrors,
}: LabelTreeViewLabelProps): JSX.Element => {
    return (
        <>
            <LabelTreeViewItemPrefix
                isOpen={isOpen}
                onOpenClickHandler={onOpenClickHandler}
                childrenLength={item.children.length}
            />
            <Flex width={'100%'} height={'100%'} alignItems={'center'}>
                <Flex alignItems='center' gap='size-100' width={'100%'}>
                    {!inEditionMode ? (
                        <LabelPresentationMode item={item as LabelTreeLabelProps} newTree={newTree} />
                    ) : (
                        <LabelEditionMode
                            item={item as LabelTreeLabelProps}
                            savedItem={savedItem as LabelTreeLabelProps}
                            save={save}
                            flatListProjectItems={flatProjectLabels}
                            domains={domains}
                            setValidationError={setValidationError}
                            validationErrors={validationErrors}
                            newTree={newTree}
                        />
                    )}
                </Flex>
            </Flex>
        </>
    );
};
