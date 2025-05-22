// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Switch, Text, Tooltip, TooltipTrigger } from '@geti/ui';

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
