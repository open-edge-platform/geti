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

import { LabelTreeItem } from '../../../../../core/labels/label-tree-view.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { SearchLabelTreeItemSuffix } from './search-label-tree-view-item.component';
import { SearchLabelTreeView } from './search-label-tree-view.component';

interface LabelResultPanelProps {
    labelsTree: LabelTreeItem[];
    onSelected: (label: Label) => void;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
}

export const LabelResultPanel = ({ suffix, prefix, onSelected, labelsTree }: LabelResultPanelProps): JSX.Element => {
    const hasLabels = !isEmpty(labelsTree);

    return (
        <View borderColor='gray-400' backgroundColor='gray-50' position={'relative'} overflow={'auto'}>
            <div aria-label='Label search results'>
                {hasLabels ? (
                    <SearchLabelTreeView
                        labels={labelsTree}
                        itemClickHandler={onSelected}
                        suffix={suffix}
                        prefix={prefix}
                    />
                ) : (
                    <Flex alignItems='center' justifyContent='center' marginTop='size-100' marginBottom='size-100'>
                        <Text>No Results</Text>
                    </Flex>
                )}
            </div>
        </View>
    );
};
