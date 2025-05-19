// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SpectrumWellProps, Well } from '@geti/ui';
import { DimensionValue } from '@geti/ui/src/dna';
import { Responsive } from '@geti/ui/src/style';

import classes from './custom-well.module.scss';

export interface CustomWellProps extends SpectrumWellProps {
    id: string;
    children: JSX.Element;
    isSelected?: boolean;
    isSelectable?: boolean;
    height?: Responsive<DimensionValue>;
    width?: Responsive<DimensionValue>;
    margin?: Responsive<DimensionValue>;
    flex?: string;
    position?: Responsive<'fixed' | 'static' | 'relative' | 'absolute' | 'sticky'>;
    className?: string;
}

export const CustomWell = ({
    children,
    position = 'static',
    isSelected = false,
    isSelectable = true,
    className,
    ...props
}: CustomWellProps): JSX.Element => {
    return (
        <Well
            position={position}
            UNSAFE_className={`${
                isSelected ? classes.selected : isSelectable ? classes.selectableWell : classes.basicWell
            } ${className}`}
            {...props}
        >
            {children}
        </Well>
    );
};
