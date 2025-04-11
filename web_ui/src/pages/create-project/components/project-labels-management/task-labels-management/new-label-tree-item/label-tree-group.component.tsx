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

import { Flex } from '@adobe/react-spectrum';

import { LabelGroup } from '../../../../../../assets/icons';
import { LabelTreeGroupProps, LabelTreeItem } from '../../../../../../core/labels/label-tree-view.interface';
import { getFlattenedItems } from '../../../../../../core/labels/utils';
import { GroupCreation } from '../../../../../../shared/components/label-tree-view/label-tree-view-item/group-edition-mode/group-creation.component';

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
