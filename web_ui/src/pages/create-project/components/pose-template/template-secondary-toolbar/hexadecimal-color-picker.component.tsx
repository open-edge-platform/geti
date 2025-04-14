// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
