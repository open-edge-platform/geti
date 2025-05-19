// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { ActionButton, Tooltip, TooltipTrigger, useNumberFormatter } from '@geti/ui';
import clsx from 'clsx';
import { useControls } from 'react-zoom-pan-pinch';

import { Add, Remove } from '../../../../../assets/icons';
import { useEventListener } from '../../../../../hooks/event-listener/event-listener.hook';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';

import classes from '../annotator-footer.module.scss';

interface ZoomLevelProps {
    zoom: number;
}

const getZoomStep = () => {
    // The zoom step is calculated based on the screen inner width, with a step value between 0.1 and 1
    // To tweak this, all we need to do is change the zoom factor value

    // 1) Calculate the biggest dimensions and find a zoom factor
    const biggestDimension = Math.max(window.innerHeight, window.innerWidth);
    const zoomFactor = 40; // Based on manual experimentation

    // 2) Get the maximum value between that calculation and 10
    const step = Math.max(Math.round(biggestDimension / zoomFactor), 10);

    // 3) Calculate the final zoom step, which will be a value between 0.1 and 1
    return Math.min(step, 100) / 100;
};

export const ZoomLevel = ({ zoom }: ZoomLevelProps): JSX.Element => {
    const { zoomIn, zoomOut, resetTransform } = useControls();
    const [zoomStep, setZoomStep] = useState(getZoomStep());

    const updateZoomStep = () => {
        const newZoomStep = getZoomStep();

        if (zoomStep !== newZoomStep) {
            setZoomStep(newZoomStep);
        }
    };

    const formatter = useNumberFormatter({
        style: 'percent',
        maximumFractionDigits: 0,
    });

    useEventListener('resize', updateZoomStep);

    return (
        <>
            <QuietActionButton
                onPress={() => {
                    zoomOut(zoomStep);
                }}
                aria-label={'Zoom out'}
            >
                <Remove />
            </QuietActionButton>
            <TooltipTrigger placement={'top'}>
                <ActionButton
                    isQuiet
                    UNSAFE_className={classes.tooltipButton}
                    onPress={() => {
                        resetTransform();
                    }}
                >
                    <span
                        className={clsx(classes.text, classes.zoomLevelValue)}
                        data-testid='zoom-level'
                        aria-label={'Zoom level'}
                        id='footer-zoom-display'
                        data-value={zoom}
                    >
                        {formatter.format(zoom)}
                    </span>
                </ActionButton>
                <Tooltip>Zoom level</Tooltip>
            </TooltipTrigger>
            <QuietActionButton
                aria-label={'Zoom in'}
                onPress={() => {
                    zoomIn(zoomStep);
                }}
            >
                <Add />
            </QuietActionButton>
        </>
    );
};
