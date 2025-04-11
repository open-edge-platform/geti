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

import { Flex } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';
import { useMediaQuery } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';

import { BoundingBox, BoundingCircle } from '../../../../assets/icons';
import { Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Label } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { NumberSliderWithLocalHandler } from '../../../../shared/components/number-slider/number-slider-with-local-handler.component';
import { Switch } from '../../../../shared/components/switch/switch.component';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { AcceptRejectButtonGroup } from '../../components/accept-reject-button-group/accept-reject-button-group.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAddUnfinishedShape } from '../../hooks/use-add-unfinished-shape.hook';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { BoundingBoxTool } from '../bounding-box';
import { CircleTool } from '../circle-tool';
import { ToolAnnotationContextProps } from '../tools.interface';
import { useApplyLabelToPendingAnnotations } from '../useApplyLabelToPendingAnnotations';
import { ShapeTypeButton } from './shape-type-button.component';
import { useSSIMState } from './ssim-state-provider.component';
import { MAX_NUMBER_ITEMS } from './util';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { activeDomains } = useTask();
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const { toolState, reset, rerun, previewThreshold, updateToolState } = useSSIMState();
    const { getToolSettings, updateToolSettings } = annotationToolContext;
    const { addShapes } = annotationToolContext.scene;

    const ssimSettings = getToolSettings(ToolType.SSIMTool);

    const sliderThreshold = previewThreshold ?? toolState.threshold;

    const isBoxToolEnabled = activeDomains.some((domain: DOMAIN) => BoundingBoxTool.supportedDomains.includes(domain));
    const isCircleToolEnabled = activeDomains.some((domain: DOMAIN) => CircleTool.supportedDomains.includes(domain));

    useAddUnfinishedShape({
        shapes: toolState.shapes,
        addShapes: (unfinishedShapes) => addShapes(unfinishedShapes as Shape[]),
        reset,
    });

    const hasResults = !isEmpty(toolState.shapes);

    const handleConfirmAnnotation = (label?: Label) => {
        addShapes(toolState.shapes, label ? [label] : undefined);

        reset();
    };

    const handleCancelAnnotation = () => {
        reset();
    };

    const handleAutoMergeDuplicatesSwitch = (value: boolean) => {
        updateToolSettings(ToolType.SSIMTool, { autoMergeDuplicates: value });
        rerun({ autoMergeDuplicates: value });
    };

    const setShapeType = (shapeType: ShapeType) => {
        updateToolSettings(ToolType.SSIMTool, { shapeType });
    };

    const updateThreshold = (threshold: number) => {
        updateToolState({ threshold }, ssimSettings.shapeType);
    };

    useApplyLabelToPendingAnnotations({
        applyAnnotations: handleConfirmAnnotation,
        annotationToolContext,
        tool: ToolType.SSIMTool,
    });

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125' marginEnd='size-125'>
            {isLargeSize && (
                <>
                    <Text>Detection assistant</Text>
                    <Divider orientation='vertical' size='S' />
                </>
            )}
            {isBoxToolEnabled && (
                <ShapeTypeButton
                    label='Bounding box mode'
                    shapeType={ShapeType.Rect}
                    currentShapeType={ssimSettings.shapeType}
                    setShapeType={() => setShapeType(ShapeType.Rect)}
                >
                    <BoundingBox />
                </ShapeTypeButton>
            )}

            {isCircleToolEnabled && (
                <ShapeTypeButton
                    label='Circle mode'
                    shapeType={ShapeType.Circle}
                    currentShapeType={ssimSettings.shapeType}
                    setShapeType={() => setShapeType(ShapeType.Circle)}
                >
                    <BoundingCircle />
                </ShapeTypeButton>
            )}
            <Divider orientation='vertical' size='S' />
            <Switch margin='0' onChange={handleAutoMergeDuplicatesSwitch} isSelected={ssimSettings.autoMergeDuplicates}>
                Auto merge duplicates
            </Switch>
            <Divider orientation='vertical' size='S' />

            {hasResults && (
                <>
                    <NumberSliderWithLocalHandler
                        min={1}
                        step={1}
                        id='number-of-items'
                        label='Detected items'
                        displayText={(number) => number}
                        onChange={updateThreshold}
                        value={sliderThreshold}
                        ariaLabel='Detection tool threshold slider'
                        isDisabled={toolState.matches.length === 1}
                        max={Math.min(MAX_NUMBER_ITEMS, toolState.matches.length)}
                        isInputEditable
                        changeAdHoc
                    />
                    <Divider orientation='vertical' size='S' />
                </>
            )}

            <AcceptRejectButtonGroup
                id={'ssim'}
                shouldShowButtons={hasResults}
                acceptDeps={[toolState.shapes]}
                handleAcceptAnnotation={() => handleConfirmAnnotation()}
                handleRejectAnnotation={handleCancelAnnotation}
            />
        </Flex>
    );
};
