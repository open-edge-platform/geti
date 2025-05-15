// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { Slider } from '@geti/ui';
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
