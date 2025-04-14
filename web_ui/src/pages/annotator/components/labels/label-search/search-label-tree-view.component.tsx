// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
