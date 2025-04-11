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

import { Flex, Switch, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';
import { useHotkeys } from 'react-hotkeys-hook';

import { RightClick } from '../../../../assets/icons';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { LoadingIndicator } from '../../../../shared/components/loading/loading-indicator.component';
import { NumberSliderWithLocalHandler } from '../../../../shared/components/number-slider/number-slider-with-local-handler.component';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { AcceptRejectButtonGroup } from '../../components/accept-reject-button-group/accept-reject-button-group.component';
import { ToolSettings, ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useSegmentAnything } from './segment-anything-state-provider.component';

const INTERACTIVE_MODE_TOOLTIP = 'With this mode ON, edit preview by placing new positive or negative points. - SHIFT';

const RIGHT_CLICK_MODE_TOOLTIP =
    'With this mode ON, press left-click to place positive points and right-click to place negative points.';

export const SecondaryToolbar = () => {
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const { getToolSettings, updateToolSettings } = useAnnotationToolContext();

    const { handleCancelAnnotation, handleConfirmAnnotation, result, points, isProcessing, isLoading, encodingQuery } =
        useSegmentAnything();

    const hasResults = !isEmpty(result.shapes) && !isEmpty(points);
    const toolSettings = getToolSettings(ToolType.SegmentAnythingTool);

    const handleOnChange = (value: number) => {
        updateToolSettings(ToolType.SegmentAnythingTool, { ...toolSettings, maskOpacity: value });
    };

    const setToolSetting = (data: Partial<ToolSettings[ToolType.SegmentAnythingTool]>) => {
        updateToolSettings(ToolType.SegmentAnythingTool, { ...toolSettings, ...data });
    };

    useHotkeys('shift', () => {
        setToolSetting({ interactiveMode: !toolSettings.interactiveMode });
    });

    if (isLoading || encodingQuery.data === undefined) {
        return (
            <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
                {isLargeSize && (
                    <>
                        <Text>Auto segmentation</Text>
                        <Divider orientation='vertical' size='S' />
                    </>
                )}

                <LoadingIndicator size={'S'} />
                <Text>{isLoading ? 'Loading image model' : 'Extracting image features'}</Text>
            </Flex>
        );
    }

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            {isLargeSize && (
                <>
                    <Text>Auto segmentation</Text>
                    <Divider orientation='vertical' size='S' />
                </>
            )}

            <TooltipTrigger placement={'bottom'}>
                <Switch
                    isSelected={toolSettings.interactiveMode}
                    onChange={(interactiveMode) => setToolSetting({ interactiveMode })}
                    height='100%'
                    aria-label='Interactive mode'
                    isDisabled={toolSettings.interactiveMode === true && points.length > 0}
                >
                    Interactive mode
                </Switch>
                <Tooltip>{INTERACTIVE_MODE_TOOLTIP}</Tooltip>
            </TooltipTrigger>

            <Divider orientation='vertical' size='S' />

            <Flex justifyContent={'center'} alignItems={'center'} marginEnd={'size-200'}>
                <TooltipTrigger placement={'bottom'}>
                    <Switch
                        margin={0}
                        isSelected={toolSettings.rightClickMode}
                        isDisabled={toolSettings.interactiveMode === false}
                        onChange={(val) => setToolSetting({ rightClickMode: val })}
                        height='100%'
                        aria-label='Right-click mode'
                    >
                        <Flex gap={'size-100'} alignContent={'center'} height={'100%'}>
                            Right-click mode
                            <View
                                paddingY={'size-25'}
                                UNSAFE_style={{
                                    color:
                                        toolSettings.rightClickMode && toolSettings.interactiveMode === true
                                            ? 'var(--spectrum-global-color-gray-900)'
                                            : 'var(--spectrum-global-color-gray-600)',
                                }}
                            >
                                <RightClick />
                            </View>
                        </Flex>
                    </Switch>

                    <Tooltip>{RIGHT_CLICK_MODE_TOOLTIP}</Tooltip>
                </TooltipTrigger>
            </Flex>

            <Divider orientation='vertical' size='S' />

            <TooltipTrigger placement={'bottom'}>
                <NumberSliderWithLocalHandler
                    id='mask-opacity'
                    displayText={(value) => `${Math.round(100 * value)}%`}
                    label={'Mask opacity'}
                    ariaLabel='Mask opacity'
                    min={0}
                    max={1}
                    step={0.01}
                    onChange={handleOnChange}
                    value={toolSettings.maskOpacity}
                />
                <Tooltip>Adjust the opacity</Tooltip>
            </TooltipTrigger>

            {points.length > 0 && (
                <>
                    <Divider orientation='vertical' size='S' />

                    <AcceptRejectButtonGroup
                        id={'segment-anything'}
                        isAcceptButtonDisabled={isProcessing || !hasResults}
                        shouldShowButtons={points.length > 0}
                        handleAcceptAnnotation={handleConfirmAnnotation}
                        handleRejectAnnotation={handleCancelAnnotation}
                        acceptDeps={[handleConfirmAnnotation]}
                        rejectDeps={[isProcessing]}
                    />
                </>
            )}
        </Flex>
    );
};
