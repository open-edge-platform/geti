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

import classes from './breadcrumb-segment.module.scss';

interface BreadcrumbSegmentProps {
    idSuffix: string;
    isSelected: boolean;
    onClick: () => void;
    text: string;
    withoutArrow?: boolean;
    isDisabled?: boolean;
}

export const BreadcrumbSegment = ({
    idSuffix,
    isSelected,
    onClick,
    text,
    withoutArrow = false,
    isDisabled = false,
}: BreadcrumbSegmentProps): JSX.Element => {
    return (
        <li id={`breadcrumb-${idSuffix}`} className={classes.breadcrumbListItem}>
            <button
                className={`${classes.breadcrumbItem} ${isSelected ? classes.selected : ''} ${
                    withoutArrow ? classes.all : ''
                } ${isDisabled ? classes.disabled : ''}`}
                onClick={onClick}
                disabled={isDisabled}
            >
                {text}
            </button>
        </li>
    );
};
