// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { GroupCreation } from '@shared/components/label-tree-view/label-tree-view-item/group-edition-mode/group-creation.component';

import { LabelGroup } from '../../../../../../assets/icons';
import { LabelTreeGroupProps, LabelTreeItem } from '../../../../../../core/labels/label-tree-view.interface';
import { getFlattenedItems } from '../../../../../../core/labels/utils';

interface LabelTreeGroupComponentProps {
    labels: LabelTreeItem[];
    save: (editedGroup: LabelTreeGroupProps) => void;
    parentGroupName: string | null;
    parentLabelId: string | null;
}

export const LabelTreeGroup = ({
    labels,
    save,
    parentGroupName,
    parentLabelId,
}: LabelTreeGroupComponentProps): JSX.Element => {
    const flatProjectItems = getFlattenedItems(labels);

    return (
        <Flex gap={'size-100'} alignItems={'center'} marginStart={'size-100'} marginY={'size-200'}>
            <Flex>
                <LabelGroup />
            </Flex>

            <GroupCreation
                save={save}
                flatProjectItems={flatProjectItems}
                parentLabelId={parentLabelId}
                parentGroupName={parentGroupName}
            />
        </Flex>
    );
};
