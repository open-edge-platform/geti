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

import { KeyboardEvent, useCallback, useEffect, useRef, useState } from 'react';

import { Item, Menu, TextField, View } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import last from 'lodash/last';

import { SearchRuleShapeType, SearchRuleValue, ShapeOption } from '../../../../core/media/media-filter.interface';
import { CustomPopover } from '../../../../shared/components/custom-popover/custom-popover.component';
import { KeyMap } from '../../../../shared/keyboard-events/keyboard.interface';
import { trimAndLowerCase } from '../../../../shared/utils';
import {
    concatByProperty,
    deleteEmptySpaceAndLastComa,
    getLowercaseSplitNames,
    getShapeTypeByKey,
    isDigit,
    isKeyboardDelete,
    SHAPE_OPTIONS,
} from '../../utils';

interface mediaFilterValueShapeProps {
    value: SearchRuleValue;
    isDisabled?: boolean;
    isMultiselection?: boolean;
    onSelectionChange: (key: SearchRuleValue) => void;
}

const hasShapeItem = (name: string) =>
    SHAPE_OPTIONS.some(({ text }) => trimAndLowerCase(text) === trimAndLowerCase(name));

const isValidShapeName = (names: string) => getLowercaseSplitNames(names).every(hasShapeItem);
const getShapesFromText = (text: SearchRuleValue) => {
    const shapes = (Array.isArray(text) ? [...text] : [String(text)]) as SearchRuleShapeType[];

    return shapes.map(getShapeTypeByKey) as ShapeOption[];
};

export const MediaFilterValueShape = ({
    value = '',
    isDisabled = false,
    isMultiselection = false,
    onSelectionChange,
}: mediaFilterValueShapeProps): JSX.Element => {
    const triggerRef = useRef(null);
    const savedShapes = useRef<ShapeOption[]>([]);
    const dialogState = useOverlayTriggerState({});
    const [inputValue, setInputValue] = useState('');

    const setInputValueAndSelectionChange = useCallback(
        (shapes: ShapeOption[], callOnSelection = true) => {
            const newShapes = isMultiselection ? [...shapes] : [last(shapes) as ShapeOption];
            const concatInputValue = concatByProperty(newShapes, 'text');
            const formatValue = isMultiselection ? concatInputValue : deleteEmptySpaceAndLastComa(concatInputValue);
            const shapesKeys = isMultiselection ? newShapes.map((shape) => shape.key) : newShapes[0]?.key;
            savedShapes.current = newShapes;

            setInputValue(formatValue);
            callOnSelection && onSelectionChange(shapesKeys ?? '');
        },
        [isMultiselection, onSelectionChange]
    );

    useEffect(() => {
        if (value === '') {
            setInputValueAndSelectionChange([], false);

            return;
        }

        setInputValueAndSelectionChange(getShapesFromText(value), false);
    }, [setInputValueAndSelectionChange, value]);

    const onSelect = (newShape: ShapeOption) => {
        dialogState.close();

        const isNewShape = getLowercaseSplitNames(inputValue).every(
            (shapeName) => shapeName !== trimAndLowerCase(newShape.text)
        );

        if (isNewShape) {
            setInputValueAndSelectionChange([...savedShapes.current, newShape]);
        }
    };

    const onKeyUp = (event: KeyboardEvent) => {
        const textValue = trimAndLowerCase((event.target as HTMLInputElement).value);
        const shapeNames = getLowercaseSplitNames(textValue);
        const newShapes = SHAPE_OPTIONS.filter((shape) => shapeNames.includes(trimAndLowerCase(shape.text)));
        const hasdifference = shapeNames.length !== newShapes.length;

        if (isDigit(event.keyCode) && isValidShapeName(textValue)) {
            setInputValueAndSelectionChange(newShapes);
        }

        if (isKeyboardDelete(event) && hasdifference) {
            setInputValueAndSelectionChange(newShapes);
        }
    };

    return (
        <View position='relative'>
            <TextField
                isQuiet
                width={'auto'}
                ref={triggerRef}
                onKeyUp={onKeyUp}
                value={inputValue}
                isDisabled={isDisabled}
                onFocus={dialogState.open}
                id='media-filter-shape-type'
                aria-label='media-filter-shape-type'
                validationState={isValidShapeName(inputValue) ? 'valid' : 'invalid'}
                onChange={(currentValue) => {
                    dialogState.open();
                    setInputValue(currentValue);
                }}
                onKeyDown={(event: KeyboardEvent) => {
                    if (event.key === KeyMap.ArrowDown) {
                        dialogState.open();
                    }
                }}
            />
            <CustomPopover state={dialogState} ref={triggerRef}>
                <Menu
                    shouldFocusWrap
                    items={SHAPE_OPTIONS}
                    aria-label='shapes-types'
                    onAction={(key) => onSelect(getShapeTypeByKey(key as SearchRuleShapeType) as ShapeOption)}
                >
                    {(item) => (
                        <Item key={item.key} aria-label={`option-${item.key}`}>
                            {item.text}
                        </Item>
                    )}
                </Menu>
            </CustomPopover>
        </View>
    );
};
