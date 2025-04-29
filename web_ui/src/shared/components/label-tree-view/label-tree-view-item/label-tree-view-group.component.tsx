// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';

import { LabelGroup } from '../../../../assets/icons';
import { LabelTreeGroupProps } from '../../../../core/labels/label-tree-view.interface';
import { filterGroups } from '../../../../core/labels/utils';
import { GroupEditionMode } from './group-edition-mode/group-edition-mode.component';
import { GroupPresentationMode } from './label-presentation-mode/group-presentation-mode.component';
import { LabelTreeViewItemPrefix } from './label-tree-view-item-prefix.component';
import { TreeViewItemContentProps, TreeViewItemEditModeProps } from './label-tree-view-item.interface';

type LabelTreeViewGroupProps = Omit<TreeViewItemEditModeProps<LabelTreeGroupProps>, 'domains'> &
    TreeViewItemContentProps;

export const LabelTreeViewGroup = ({
    item,
    savedItem,
    save,
    newTree,
    isOpen,
    onOpenClickHandler,
    inEditionMode,
    flatListProjectItems: flatProjectItems,
    setValidationError,
    validationErrors,
}: LabelTreeViewGroupProps): JSX.Element => {
    const flatProjectGroups = filterGroups(flatProjectItems);

    return (
        <>
            <Flex width={'100%'} alignItems={'center'} height={'100%'} minHeight={'4.4rem'}>
                <LabelTreeViewItemPrefix
                    isOpen={isOpen}
                    onOpenClickHandler={onOpenClickHandler}
                    childrenLength={item.children.length}
                />

                <Flex alignItems='center' gap='size-100' width={'100%'}>
                    <LabelGroup />

                    {!inEditionMode ? (
                        <GroupPresentationMode item={item as LabelTreeGroupProps} newTree={newTree} />
                    ) : (
                        <GroupEditionMode
                            flatListProjectItems={flatProjectGroups}
                            item={item as LabelTreeGroupProps}
                            savedItem={savedItem as LabelTreeGroupProps}
                            save={save}
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
