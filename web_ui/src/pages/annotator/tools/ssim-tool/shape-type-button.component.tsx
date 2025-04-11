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
