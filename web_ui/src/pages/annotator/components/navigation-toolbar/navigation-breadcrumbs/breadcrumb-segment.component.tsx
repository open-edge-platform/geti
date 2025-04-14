// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
