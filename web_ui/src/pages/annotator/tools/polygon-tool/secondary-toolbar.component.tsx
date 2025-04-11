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

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { Divider } from '../../../../shared/components/divider/divider.component';
import { Switch } from '../../../../shared/components/switch/switch.component';
import { useDrawingToolsKeyboardShortcut } from '../../../annotator/hot-keys/use-drawing-tools-keyboard-shortcut/use-drawing-tools-keyboard-shortcut';
import { ToolAnnotationContextProps } from '../tools.interface';
import { blurActiveInput } from '../utils';
import { usePolygonState } from './polygon-state-provider.component';
import { PolygonMode } from './polygon-tool.enum';

export const SecondaryToolbar = (_annotationToolContext: ToolAnnotationContextProps): JSX.Element => {
    const { mode, setMode, isIntelligentScissorsLoaded } = usePolygonState();
    const isDisabled = !isIntelligentScissorsLoaded;
    const isMagneticLasso = !!mode && [PolygonMode.MagneticLasso, PolygonMode.MagneticLassoClose].includes(mode);

    const onChangeSnappingMode = (isSelected: boolean) =>
        setMode(isSelected ? PolygonMode.MagneticLasso : PolygonMode.Polygon);

    const handleToggleSnappingMode = () => onChangeSnappingMode(!isMagneticLasso);

    useDrawingToolsKeyboardShortcut(PolygonMode.MagneticLasso, handleToggleSnappingMode, isDisabled, [
        mode,
        isIntelligentScissorsLoaded,
    ]);

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            <Text>Polygon Tool</Text>
            <Divider orientation='vertical' size='S' />

            <TooltipTrigger placement={'bottom'}>
                <Switch
                    isSelected={isMagneticLasso}
                    isDisabled={isDisabled}
                    onFocusChange={blurActiveInput}
                    onChange={onChangeSnappingMode}
                >
                    Snapping mode
                </Switch>
                <Tooltip>{`SHIFT+S`}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
