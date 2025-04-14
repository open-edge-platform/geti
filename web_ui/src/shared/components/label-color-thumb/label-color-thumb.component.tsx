// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../../../core/labels/label.interface';
import { isEmptyLabel } from '../../../core/labels/utils';
import { ColorThumb, ColorThumbProps } from '../color-thumb/color-thumb.component';

interface LabelColorThumbProps extends Omit<ColorThumbProps, 'color'> {
    label: Label;
}

export const LabelColorThumb = ({ label, ...rest }: LabelColorThumbProps): JSX.Element => {
    if (isEmptyLabel(label)) {
        return <></>;
    }

    return <ColorThumb color={label.color} {...rest} />;
};
