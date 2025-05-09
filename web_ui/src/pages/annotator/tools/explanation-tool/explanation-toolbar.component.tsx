// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Flex, Item, Picker } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../core/annotations/prediction.interface';
import { Label } from '../../../../core/labels/label.interface';
import { getNonEmptyLabelsFromProject } from '../../../../core/labels/utils';
import { CANVAS_ADJUSTMENTS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { TooltipWithDisableButton } from '../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { NumberSlider } from '../../../../shared/components/number-slider/number-slider.component';
import { Switch } from '../../../../shared/components/switch/switch.component';
import { hasEqualId } from '../../../../shared/utils';
import { isEmptyLabelAnnotation } from '../../../utils';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotatorCanvasSettings } from '../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import {
    useExplanationOpacity,
    usePrediction,
} from '../../providers/prediction-provider/prediction-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { SelectModel } from './select-model.component';
import { activeExplanationTooltip } from './utils';

import classes from './explanation-tool.module.scss';

type FormattedExplanation = Explanation & { labelName: string };

export interface ExplanationSecondaryToolbarProps {
    isDisabled?: boolean;
    explanations: Explanation[];
    disabledTooltip?: string;
}

export const OVERLAP_LABEL_OPACITY = 0.8;
export const formatExplanations = (labels: Label[], explanations?: Explanation[]): FormattedExplanation[] => {
    return (
        explanations?.map((explanation) => {
            const matchLabel = labels.find(hasEqualId(explanation.labelsId));
            const labelName = matchLabel?.name ?? explanation.name;
            return { ...explanation, labelName };
        }) ?? []
    );
};

const filterExplanationByAnnotation = (
    explanations: FormattedExplanation[],
    annotations: readonly Annotation[]
): FormattedExplanation[] => {
    const [selectedAnnotation] = annotations.filter(({ isSelected }) => isSelected);

    return explanations.filter(({ roi }) => roi.id === selectedAnnotation?.id);
};

export const ExplanationToolbar = ({
    isDisabled = false,
    explanations,
    disabledTooltip = '',
}: ExplanationSecondaryToolbarProps): JSX.Element => {
    const { scene } = useAnnotationToolContext();
    const { canvasSettingsState } = useAnnotatorCanvasSettings();
    const { tasks, isTaskChainSecondTask } = useTask();
    const { explanationOpacity, setExplanationOpacity, showOverlapAnnotations, setShowOverlapAnnotations } =
        useExplanationOpacity();

    const {
        isExplanationVisible,
        selectedExplanation,
        predictionAnnotations,
        setExplanationVisible,
        setSelectedExplanation,
    } = usePrediction();

    const labels = getNonEmptyLabelsFromProject(tasks);
    const [canvasSettings, handleCanvasSetting] = canvasSettingsState;
    const formattedExplanations = formatExplanations(labels, explanations);
    const labelOpacityConfig = canvasSettings[CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY];
    const hasEmptyLabelPredictions = predictionAnnotations.some(isEmptyLabelAnnotation);
    const finalExplanations = isTaskChainSecondTask
        ? filterExplanationByAnnotation(formattedExplanations, scene.annotations)
        : formattedExplanations;

    return (
        <Flex
            wrap='nowrap'
            height='100%'
            alignItems='center'
            gap={{ base: 'size-100', L: 'size-150' }}
            marginStart={{ base: '0px', L: 'size-150' }}
        >
            <SelectModel />

            <TooltipWithDisableButton disabledTooltip={disabledTooltip} activeTooltip={activeExplanationTooltip}>
                <Switch
                    margin={0}
                    isDisabled={isDisabled || hasEmptyLabelPredictions || isEmpty(finalExplanations)}
                    isSelected={isExplanationVisible}
                    aria-label='explanation-switcher'
                    onChange={setExplanationVisible}
                >
                    Explanation
                </Switch>
            </TooltipWithDisableButton>

            <Picker
                width={{ base: 'size-1200', L: 'size-1600' }}
                placeholder='Select Label'
                aria-label='show explanations dropdown'
                data-testid='show-explanations-dropdown'
                items={finalExplanations}
                selectedKey={selectedExplanation?.id}
                isDisabled={!isExplanationVisible}
                UNSAFE_className={classes.secondaryToolbarMapPicker}
                onSelectionChange={(key: Key) => {
                    const stringKey = key.toString();
                    const selectedMap = finalExplanations.find(hasEqualId(stringKey));
                    selectedMap && setSelectedExplanation(selectedMap);
                }}
            >
                {(item: FormattedExplanation) => (
                    <Item key={item.id} aria-label={item.labelName}>
                        {item.labelName}
                    </Item>
                )}
            </Picker>

            <NumberSlider
                id='opacity-slider'
                min={0}
                step={1}
                max={100}
                label='Opacity'
                ariaLabel='opacity'
                isDisabled={!isExplanationVisible}
                value={explanationOpacity}
                onChange={setExplanationOpacity}
                displayText={(value) => `${value}%`}
            />

            <Divider orientation='vertical' size={'S'} />
            <Switch
                margin={0}
                isSelected={showOverlapAnnotations}
                onChange={(isOn) => {
                    const labelOpacity = isOn ? OVERLAP_LABEL_OPACITY : labelOpacityConfig.defaultValue;

                    setShowOverlapAnnotations(isOn);
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY, labelOpacity);
                }}
                aria-label='overlap annotations'
                isDisabled={isExplanationVisible}
            >
                Annotations
            </Switch>
            <Divider orientation='vertical' size={'S'} />
        </Flex>
    );
};
