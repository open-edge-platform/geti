// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
