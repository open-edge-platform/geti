// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';

interface ShapeTypeButtonProps {
    label: string;
    currentShapeType: ShapeType;
    shapeType: ShapeType;
    setShapeType: (shapeType: ShapeType) => void;
    isDisabled?: boolean;
    children: ReactNode;
}

export const ShapeTypeButton = ({
    label,
    currentShapeType,
    shapeType,
    setShapeType,
    children,
    isDisabled = false,
}: ShapeTypeButtonProps) => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietToggleButton
                id={label}
                aria-label={label}
                isDisabled={isDisabled}
                onPress={() => setShapeType(shapeType)}
                isSelected={currentShapeType === shapeType}
            >
                {children}
            </QuietToggleButton>
            <Tooltip>{label}</Tooltip>
        </TooltipTrigger>
    );
};
