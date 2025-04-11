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

import { useState } from 'react';

import { Content, Dialog, DialogTrigger, Flex } from '@adobe/react-spectrum';
import { HexColorInput, HexColorPicker } from 'react-colorful';

import { Button } from '../../../../../shared/components/button/button.component';
import { ChangeColorButton } from '../../../../../shared/components/change-color-button/change-color-button.component';
import { validateColor } from '../utils';

import classes from './color-picker-dialog.module.scss';

interface ColorPickerDialogProps {
    id: string;
    color: string | undefined;
    onColorChange: (color: string) => void;
    ariaLabelPrefix?: string;
    size?: 'S' | 'L';
    onOpenChange?: (isOpen: boolean) => void;
    gridArea?: string;
}

export const ColorPickerDialog = ({
    id,
    color,
    onColorChange,
    ariaLabelPrefix,
    size = 'L',
    onOpenChange = () => {
        /**/
    },
    gridArea,
}: ColorPickerDialogProps): JSX.Element => {
    const [selectedColor, setSelectedColor] = useState<string | undefined>(color);
    const [inputColor, setInputColor] = useState<string | undefined>(color);

    const confirmColor = () => {
        if (selectedColor) {
            onColorChange(selectedColor);
            setInputColor(selectedColor);
        }
    };

    // eslint-disable-next-line
    const handleOnChange = (e: any) => {
        const newColor = validateColor(`#${e.currentTarget.value}`);
        setSelectedColor(newColor);
    };

    return (
        <DialogTrigger type='popover' onOpenChange={onOpenChange}>
            <ChangeColorButton
                id={id}
                ariaLabelPrefix={ariaLabelPrefix}
                size={size}
                color={color}
                gridArea={gridArea}
            />
            {(close) => (
                <Dialog UNSAFE_className={classes.dialog}>
                    <Content>
                        <Flex
                            direction={'column'}
                            margin={'size-400'}
                            marginBottom={'size-200'}
                            gap={'size-200'}
                            UNSAFE_style={{ width: 'fit-content' }}
                        >
                            <HexColorPicker
                                color={selectedColor}
                                onChange={(input) => {
                                    setSelectedColor(input);
                                    setInputColor(input);
                                }}
                            />
                            <HexColorInput
                                color={inputColor}
                                className={classes.colorHexInput}
                                id={`${id}-color-input`}
                                data-testid={`${id}-color-input`}
                                onKeyUp={handleOnChange}
                            />
                            <Flex gap={'size-100'} justifyContent={'center'} width={'100%'}>
                                <Button variant={'secondary'} onPress={close}>
                                    Close
                                </Button>
                                <Button
                                    variant={'primary'}
                                    onPress={() => {
                                        confirmColor();
                                        close();
                                    }}
                                >
                                    Confirm
                                </Button>
                            </Flex>
                        </Flex>
                    </Content>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
