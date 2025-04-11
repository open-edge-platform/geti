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

import { Flex, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';
import isNil from 'lodash/isNil';

import { RightClick } from '../../../../assets/icons';
import { Shape } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { Switch } from '../../../../shared/components/switch/switch.component';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { AcceptRejectButtonGroup } from '../../components/accept-reject-button-group/accept-reject-button-group.component';
import { ToolSettings, ToolType } from '../../core/annotation-tool-context.interface';
import { useAddUnfinishedShape } from '../../hooks/use-add-unfinished-shape.hook';
import { ToolAnnotationContextProps } from '../tools.interface';
import { useApplyLabelToPendingAnnotations } from '../useApplyLabelToPendingAnnotations';
import { useRITMState } from './ritm-state-provider.component';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps) => {
    const { addShapes } = annotationToolContext.scene;
    const { reset, result, isLoading, isProcessing } = useRITMState();
    const { getToolSettings, updateToolSettings } = annotationToolContext;
    const ritmSettings = getToolSettings(ToolType.RITMTool);
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const hasResults = !isNil(result);

    useAddUnfinishedShape({
        shapes: result && result.shape ? [result.shape] : [],
        addShapes: (unfinishedShapes) => addShapes(unfinishedShapes as Shape[]),
        reset,
    });

    const acceptShapes = (label?: Label) => {
        if (result && result.shape) {
            addShapes([result.shape], label ? [label] : undefined);
            reset();
        }
    };

    const handleConfirmAnnotation = () => {
        if (isProcessing) {
            return;
        }

        hasResults && acceptShapes();
        reset();
    };

    const handleCancelAnnotation = () => {
        if (!isProcessing) {
            reset();
        }
    };

    const setToolSetting = (data: Partial<ToolSettings[ToolType.RITMTool]>) => {
        updateToolSettings(ToolType.RITMTool, { ...ritmSettings, ...data });
    };

    useApplyLabelToPendingAnnotations({
        applyAnnotations: acceptShapes,
        annotationToolContext,
        tool: ToolType.RITMTool,
    });

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            {isLargeSize && <Text>Interactive segmentation</Text>}

            {isLoading && (
                <>
                    <Divider orientation='vertical' size='S' />
                    <Text>Loading...</Text>
                </>
            )}

            {!isLoading && (
                <>
                    <Divider orientation='vertical' size='S' />
                    <Switch
                        UNSAFE_style={{ margin: 0 }}
                        isSelected={ritmSettings.dynamicBoxMode}
                        onChange={(val) => setToolSetting({ dynamicBoxMode: val })}
                    >
                        Dynamic selection mode
                    </Switch>
                    <Divider orientation='vertical' size='S' />

                    <Flex
                        alignItems={'center'}
                        UNSAFE_style={{ color: ritmSettings.rightClickMode ? 'white' : '#8E9099' }}
                    >
                        <TooltipTrigger placement={'bottom'}>
                            <Switch
                                margin={0}
                                isSelected={ritmSettings.rightClickMode}
                                onChange={(val) => setToolSetting({ rightClickMode: val })}
                            >
                                Right-click mode
                            </Switch>
                            <Tooltip>
                                With this mode ON press left-click to place positive points and right-click to place
                                negative points.
                            </Tooltip>
                        </TooltipTrigger>
                        <RightClick />
                    </Flex>

                    {hasResults && <Divider orientation='vertical' size='S' />}

                    <AcceptRejectButtonGroup
                        id={'ritm'}
                        rejectDeps={[isProcessing]}
                        acceptDeps={[isProcessing]}
                        shouldShowButtons={hasResults}
                        handleAcceptAnnotation={handleConfirmAnnotation}
                        handleRejectAnnotation={handleCancelAnnotation}
                    />
                </>
            )}
        </Flex>
    );
};
