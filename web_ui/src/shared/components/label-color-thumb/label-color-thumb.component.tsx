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
