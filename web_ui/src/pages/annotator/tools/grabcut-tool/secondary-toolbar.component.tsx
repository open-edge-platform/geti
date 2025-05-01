// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';
import { Divider } from '@shared/components/divider/divider.component';
import { NumberSliderWithLocalHandler } from '@shared/components/number-slider/number-slider-with-local-handler.component';

import { Combine, New, Subtract } from '../../../../assets/icons';
import { Label } from '../../../../core/labels/label.interface';
import { AcceptRejectButtonGroup } from '../../components/accept-reject-button-group/accept-reject-button-group.component';
import { ToolToggleButton } from '../../components/primary-toolbar/tool-toggle-button.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { useApplyLabelToPendingAnnotations } from '../useApplyLabelToPendingAnnotations';
import { SENSITIVITY_SLIDER_TOOLTIP } from '../utils';
import { useGrabcutState } from './grabcut-state-provider.component';
import { GrabcutToolType } from './grabcut-tool.enums';
import { calcStrokeWidth, sensitivityConfig, sensitivityOptions } from './util';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { scene, getToolSettings, updateToolSettings } = annotationToolContext;
    const { image } = useROI();
    const { toolsState, setToolsState, rejectAnnotation, resetConfig, isLoading, loadingRect, runGrabcut } =
        useGrabcutState();
    const grabcutSettings = getToolSettings(ToolType.GrabcutTool);
    const shouldShowActionButtons = toolsState.polygon !== null;

    const updateAndRunGrabcut = (sensitivity: number): void => {
        updateToolSettings(ToolType.GrabcutTool, { sensitivity });

        const strokeWidth = calcStrokeWidth(loadingRect.current?.width ?? 0);

        runGrabcut(image, strokeWidth, sensitivity);
    };

    const acceptShapes = (label?: Label) => {
        if (toolsState.polygon) {
            scene.addShapes([toolsState.polygon], label ? [label] : undefined);

            resetConfig();
        }
    };

    useApplyLabelToPendingAnnotations({
        applyAnnotations: acceptShapes,
        annotationToolContext,
        tool: ToolType.GrabcutTool,
    });

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            <Text>Quick selection</Text>

            <Divider orientation='vertical' size='S' />

            <ToolToggleButton
                type={GrabcutToolType.InputTool}
                label={'New selection'}
                isDisabled={isLoading}
                placement='bottom'
                isActive={toolsState.activeTool === GrabcutToolType.InputTool}
                onSelect={() => setToolsState((prev) => ({ ...prev, activeTool: GrabcutToolType.InputTool }))}
            >
                <New />
            </ToolToggleButton>
            <ToolToggleButton
                type={GrabcutToolType.ForegroundTool}
                label={'Add to selection'}
                isDisabled={!toolsState.polygon || isLoading}
                placement='bottom'
                isActive={toolsState.activeTool === GrabcutToolType.ForegroundTool}
                onSelect={() => setToolsState((prev) => ({ ...prev, activeTool: GrabcutToolType.ForegroundTool }))}
            >
                <Combine />
            </ToolToggleButton>
            <ToolToggleButton
                type={GrabcutToolType.BackgroundTool}
                label={'Subtract from selection'}
                isDisabled={!toolsState.polygon || isLoading}
                placement='bottom'
                isActive={toolsState.activeTool === GrabcutToolType.BackgroundTool}
                onSelect={() => setToolsState((prev) => ({ ...prev, activeTool: GrabcutToolType.BackgroundTool }))}
            >
                <Subtract />
            </ToolToggleButton>

            <Divider orientation='vertical' size='S' />

            <TooltipTrigger placement={'bottom'}>
                <NumberSliderWithLocalHandler
                    id='sensitivity'
                    isDisabled={isLoading}
                    displayText={(val: number) => sensitivityOptions[val]}
                    label={'Sensitivity'}
                    ariaLabel='Sensitivity'
                    min={sensitivityConfig.min}
                    max={sensitivityConfig.max}
                    step={sensitivityConfig.step}
                    onChange={updateAndRunGrabcut}
                    value={grabcutSettings.sensitivity}
                />
                <Tooltip>{SENSITIVITY_SLIDER_TOOLTIP}</Tooltip>
            </TooltipTrigger>

            {shouldShowActionButtons && <Divider orientation='vertical' size='S' />}

            <AcceptRejectButtonGroup
                id={'grabcut'}
                shouldShowButtons={shouldShowActionButtons}
                handleAcceptAnnotation={() => acceptShapes()}
                handleRejectAnnotation={rejectAnnotation}
            />
        </Flex>
    );
};
