// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ButtonGroup, ToggleButton, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { AICPUIcon, Human } from '../../../../assets/icons';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';

import classes from './preview-canvas-content.module.scss';

interface ToggleModePros {
    mode: ANNOTATOR_MODE;
    setMode: (mode: ANNOTATOR_MODE) => void;
}
export const ToggleMode = ({ mode, setMode }: ToggleModePros): JSX.Element => {
    const { isExplanationVisible, setExplanationVisible } = usePrediction();

    const checkIfAnnotationMode = (m: ANNOTATOR_MODE) => {
        return m === ANNOTATOR_MODE.ACTIVE_LEARNING;
    };

    const handleToggleChange = (toggleMode: ANNOTATOR_MODE) => {
        setMode(toggleMode);
        if (isExplanationVisible && checkIfAnnotationMode(toggleMode)) {
            setExplanationVisible(false);
        }
    };

    const isAnnotationMode = checkIfAnnotationMode(mode);

    return (
        <ButtonGroup>
            <TooltipTrigger>
                <ToggleButton
                    id='select-annotation-mode'
                    aria-label='Select annotation mode'
                    isSelected={isAnnotationMode}
                    onPress={() => {
                        handleToggleChange(ANNOTATOR_MODE.ACTIVE_LEARNING);
                    }}
                    UNSAFE_className={classes.toggleAnnotatorMode}
                >
                    <Human />
                </ToggleButton>
                <Tooltip>User annotation mode</Tooltip>
            </TooltipTrigger>
            <TooltipTrigger>
                <ToggleButton
                    id='select-prediction-mode'
                    aria-label='Select prediction mode'
                    isSelected={!isAnnotationMode}
                    onPress={() => {
                        handleToggleChange(ANNOTATOR_MODE.PREDICTION);
                    }}
                    UNSAFE_className={classes.toggleAnnotatorMode}
                >
                    <AICPUIcon />
                </ToggleButton>
                <Tooltip>AI prediction mode</Tooltip>
            </TooltipTrigger>
        </ButtonGroup>
    );
};
