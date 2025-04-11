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

import { Dispatch, SetStateAction } from 'react';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import isFunction from 'lodash/isFunction';

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
