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

import { LabelTreeItem, LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { SearchLabelTreeItemSuffix, SearchLabelTreeViewItem } from './search-label-tree-view-item.component';

import classes from './search-label-tree-view-item.module.scss';

interface LabelTreeViewProps {
    itemClickHandler: (label: Label) => void;
    labels: LabelTreeItem[];
    width?: number | string;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
}

export const SearchLabelTreeView = ({
    labels,
    itemClickHandler,
    width,
    suffix,
    prefix,
}: LabelTreeViewProps): JSX.Element => {
    return (
        <ul
            className={`${classes['spectrum-TreeView']} ${classes['spectrum-TreeView--thumbnail']}`}
            style={{ margin: 0, maxWidth: width || '100%' }}
        >
            {labels.map((label: LabelTreeItem) => {
                return (
                    <SearchLabelTreeViewItem
                        key={label.id}
                        label={label as LabelTreeLabelProps}
                        clickHandler={itemClickHandler}
                        suffix={suffix}
                        prefix={prefix}
                    >
                        {label.children ? (
                            <SearchLabelTreeView
                                labels={label.children as LabelTreeLabelProps[]}
                                itemClickHandler={itemClickHandler}
                                width={width}
                                suffix={suffix}
                                prefix={prefix}
                            />
                        ) : (
                            <></>
                        )}
                    </SearchLabelTreeViewItem>
                );
            })}
        </ul>
    );
};
