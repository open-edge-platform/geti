// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Color, ColorEditor, ColorPicker } from '@adobe/react-spectrum';

import { useDebouncedCallback } from '../../../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { rgbToHex } from '../util';

interface HexadecimalColorPickerProps {
    value: string;
    onChangeEnded: (color: string) => void;
}

export const HexadecimalColorPicker = ({ value, onChangeEnded }: HexadecimalColorPickerProps) => {
    const [color, setColor] = useState<string | Color>(value);

    const debouncedChangeEnded = useDebouncedCallback((newColor: Color) => {
        const rgb = newColor.toFormat('rgb');
        const hexColor = rgbToHex(
            rgb.getChannelValue('red'),
            rgb.getChannelValue('green'),
            rgb.getChannelValue('blue')
        );

        onChangeEnded(hexColor);
    }, 150);

    const handleLabelColor = (newColor: Color) => {
        setColor(newColor);
        debouncedChangeEnded(newColor);
    };

    return (
        <ColorPicker value={color} onChange={handleLabelColor} aria-label='color selector'>
            <ColorEditor hideAlphaChannel />
        </ColorPicker>
    );
};
