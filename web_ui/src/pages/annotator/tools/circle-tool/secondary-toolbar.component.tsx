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

import { Flex, Slider } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { Divider } from '../../../../shared/components/divider/divider.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { ToolAnnotationContextProps } from '../tools.interface';
import { useCircleState } from './circle-state-provider.component';
import { MIN_RADIUS } from './utils';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { updateToolSettings } = annotationToolContext;
    const { setIsBrushSizePreviewVisible, circleRadiusSize, setCircleRadiusSize, maxCircleRadius } = useCircleState();

    const handleSizeChange = (value: number) => {
        setIsBrushSizePreviewVisible(true);
        setCircleRadiusSize(value);
    };

    const handleSizeChangeEnd = (value: number) => {
        updateToolSettings(ToolType.CircleTool, { size: value });

        setIsBrushSizePreviewVisible(false);
    };

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            <Text>Circle Tool</Text>
            <Divider orientation='vertical' size='S' />
            <Slider
                aria-label={'Circle radius'}
                label='Circle radius'
                value={circleRadiusSize}
                onChange={handleSizeChange}
                onChangeEnd={handleSizeChangeEnd}
                minValue={MIN_RADIUS}
                maxValue={maxCircleRadius}
                labelPosition='side'
                getValueLabel={(value) => `${value}px`}
            />
        </Flex>
    );
};
