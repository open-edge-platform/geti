// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Divider, Flex, Item, Picker, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';

import { Label } from '../../../../../core/labels/label.interface';
import { TooltipWithDisableButton } from '../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { NumberSliderWithLocalHandler } from '../../../../../shared/components/number-slider/number-slider-with-local-handler.component';
import { Switch } from '../../../../../shared/components/switch/switch.component';
import { hasEqualId } from '../../../../../shared/utils';
import { ToggleVisibilityButton } from '../../../../annotator/annotation/toggle-visibility-button/toggle-visibility-button.component';
import { CanvasAdjustments } from '../../../../annotator/components/primary-toolbar/canvas-adjustments/canvas-adjustments.component';
import { ANNOTATOR_MODE } from '../../../../annotator/core/annotation-tool-context.interface';
import { activeExplanationTooltip } from '../../../../annotator/tools/explanation-tool/utils';
import { isEmptyLabelAnnotation } from '../../../../utils';
import { useQuickInference } from './quick-inference-provider.component';
import { UploadImageButton } from './upload-image-button.component';

import classes from '../project-tests.module.scss';

interface SecondaryToolbarProps {
    labels: Label[];
    shouldShowExplanation: boolean;
}

export const SecondaryToolbar = ({ labels, shouldShowExplanation }: SecondaryToolbarProps): JSX.Element => {
    const {
        isDisabled,
        explanation,
        explanations,
        setExplanation,
        handleUploadImage,
        showExplanation,
        setShowExplanation,
        toggleShowPredictions,
        showPredictions,
        explanationOpacity,
        setExplanationOpacity,
        annotations: predictionAnnotations,
    } = useQuickInference();

    const selectedKey = explanation?.id || 'none';
    const hasEmptyExplanations = showExplanation && isEmpty(explanations);
    const hasEmptyLabelPredictions = predictionAnnotations.some(isEmptyLabelAnnotation);
    const mapItems = explanations.map(({ id, labelsId }) => ({ id, name: labels.find(hasEqualId(labelsId))?.name }));

    return (
        <Flex
            alignItems='center'
            aria-label='AnnotatorPreviewToolbar'
            width={'100%'}
            justifyContent={'space-between'}
            UNSAFE_className={classes.secondaryToolbar}
        >
            <Flex gap='size-225' alignItems='center'>
                {shouldShowExplanation && (
                    <>
                        <Flex alignItems='center' height='100%' gap='size-150' wrap='nowrap'>
                            <TooltipTrigger placement={'bottom'}>
                                <Switch
                                    isDisabled={isDisabled || hasEmptyLabelPredictions}
                                    isSelected={showExplanation}
                                    onChange={setShowExplanation}
                                    aria-label='explanation-switcher'
                                >
                                    <Text UNSAFE_className={classes.secondaryToolbarTextEntry}>Explanation</Text>
                                </Switch>
                                <Tooltip>{activeExplanationTooltip}</Tooltip>
                            </TooltipTrigger>
                            <Divider size='S' orientation='vertical' marginY='size-100' />
                        </Flex>
                        <Flex
                            alignItems='center'
                            height='100%'
                            gap='size-100'
                            maxWidth='static-size-4600'
                            wrap='nowrap'
                        >
                            <Text UNSAFE_className={classes.textEntryClass}>Labels:</Text>
                            <TooltipWithDisableButton
                                placement={'top'}
                                disabledTooltip={'No explanations were generated'}
                            >
                                <Picker
                                    items={mapItems}
                                    selectedKey={selectedKey}
                                    maxWidth='size-1600'
                                    placeholder='Select explanation'
                                    aria-label='show explanations dropdown'
                                    isDisabled={!showExplanation || isDisabled || hasEmptyExplanations}
                                    UNSAFE_className={classes.secondaryToolbarMapPicker}
                                    onSelectionChange={(key: Key) => {
                                        const selectedExplanation = explanations.find(hasEqualId(String(key)));
                                        setExplanation(selectedExplanation);
                                    }}
                                >
                                    {(item) => (
                                        <Item key={item.id} aria-label={item.name} textValue={item.name}>
                                            {item.name}
                                        </Item>
                                    )}
                                </Picker>
                            </TooltipWithDisableButton>
                        </Flex>

                        <Flex alignItems='center' justifyContent='center' height='100%' wrap='nowrap'>
                            <NumberSliderWithLocalHandler
                                id='opacity-slider'
                                min={0}
                                step={1}
                                max={100}
                                label='Opacity'
                                ariaLabel='opacity slider'
                                isDisabled={!showExplanation || isDisabled || hasEmptyExplanations}
                                value={explanationOpacity}
                                onChange={setExplanationOpacity}
                                displayText={(value) => `${value}%`}
                            />
                        </Flex>
                    </>
                )}
            </Flex>
            <Flex direction='row' gap='size-150'>
                <TooltipTrigger placement={'bottom'}>
                    <UploadImageButton isDisabled={isDisabled} handleUploadImage={handleUploadImage} />
                    <Tooltip>Upload image</Tooltip>
                </TooltipTrigger>

                <TooltipTrigger placement={'bottom'}>
                    <ToggleVisibilityButton
                        id={'predictions-visibility-id'}
                        onPress={toggleShowPredictions}
                        isHidden={!showPredictions}
                        mode={ANNOTATOR_MODE.PREDICTION}
                    />
                    <Tooltip>Hide predictions</Tooltip>
                </TooltipTrigger>

                <CanvasAdjustments />
            </Flex>
        </Flex>
    );
};
