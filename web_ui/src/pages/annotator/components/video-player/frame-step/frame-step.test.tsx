// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { isFunction } from 'lodash-es';

import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { FrameStep } from './frame-step.component';

it('toggles to all frames', async () => {
    const setStepState = jest.fn();
    const currentStep = 60;
    const setStep: Dispatch<SetStateAction<number>> = (updateStep) => {
        setStepState(isFunction(updateStep) ? updateStep(currentStep) : updateStep);
    };
    render(<FrameStep isDisabled={false} step={currentStep} setStep={setStep} defaultFps={currentStep} />);

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    expect(screen.getByTestId('frame-mode-indicator-id')).toHaveTextContent('1/1');
    fireEvent.click(screen.getByRole('button'));

    expect(setStepState).toHaveBeenCalledWith(1);
});

it('toggles to 1 frame per second', async () => {
    const setStepState = jest.fn();
    const step = 1;
    const setStep: Dispatch<SetStateAction<number>> = (updateStep) => {
        setStepState(isFunction(updateStep) ? updateStep(step) : updateStep);
    };

    render(<FrameStep isDisabled={false} step={step} setStep={setStep} defaultFps={60} />);

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    expect(screen.getByTestId('frame-mode-indicator-id')).toHaveTextContent('ALL');
    fireEvent.click(screen.getByRole('button'));

    expect(setStepState).toHaveBeenCalledWith(60);
});
