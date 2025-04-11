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

import { fireEvent, screen } from '@testing-library/react';

import { mockedEditableConfigTaskChainData } from '../../../../../../core/configurable-parameters/services/test-utils';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';
import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { RESHUFFLE_SUBSETS_TOOLTIP_MSG } from '../utils';
import { TrainConfigurableParameters } from './train-configurable-parameters.component';

describe('TrainConfigurableParameters', () => {
    const [learningParametersComponent] = mockedEditableConfigTaskChainData.components.filter(
        ({ header }) => header === 'Learning Parameters'
    );
    const [componentOtherThanLP] = mockedEditableConfigTaskChainData.components.filter(
        ({ header }) => header === 'Optimization By POT'
    );

    const learningParameters = learningParametersComponent.parameters || [];
    const parametersOtherThanLP = componentOtherThanLP.parameters || [];

    const setConfigParameters = jest.fn();
    const setTrainFromScratch = jest.fn();
    const updateParameter = jest.fn();
    const onChangeReshuffleSubsets = jest.fn();

    const renderTrainingConfigParams = async ({
        trainFromScratch = false,
        isReshufflingSubsetsEnabled = false,
    }: {
        trainFromScratch?: boolean;
        isReshufflingSubsetsEnabled?: boolean;
    }): Promise<void> => {
        render(
            <TrainConfigurableParameters
                configParameters={mockedEditableConfigTaskChainData}
                setConfigParameters={setConfigParameters}
                setTrainFromScratch={setTrainFromScratch}
                trainFromScratch={trainFromScratch}
                isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                onChangeReshuffleSubsets={onChangeReshuffleSubsets}
                animationDirection={-1}
                updateParameter={updateParameter}
                modelTemplateId={'detection_yolo'}
                taskId={'task-id'}
            />
        );

        fireEvent.click(await screen.findByTestId('learning-parameters-id'));
    };

    it('Learning parameters should be in the edit mode', async () => {
        await renderTrainingConfigParams({});

        learningParameters.forEach(({ header }) => {
            expect(screen.getByText(header)).toBeInTheDocument();
            const resetButtonId = `${idMatchingFormat(header)}-reset-button-id`;
            expect(screen.getByTestId(resetButtonId)).toBeInTheDocument();
        });

        fireEvent.click(screen.getByTestId('optimization-by-pot-id'));

        parametersOtherThanLP.forEach(({ header }) => {
            expect(screen.getByText(header)).toBeInTheDocument();
            const resetButtonId = `${idMatchingFormat(header)}-reset-button-id`;
            expect(screen.getByTestId(resetButtonId)).toBeInTheDocument();
        });
    });

    it('Reshuffle subsets should not be disabled when training from scratch is enabled', async () => {
        await renderTrainingConfigParams({
            trainFromScratch: true,
        });

        expect(screen.getByRole('checkbox', { name: /train from scratch/i })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: /reshuffle subsets/i })).toBeEnabled();

        fireEvent.click(screen.getByTestId('reshuffle-subsets-tooltip-id'));
        expect(await screen.findByRole('dialog')).toHaveTextContent(RESHUFFLE_SUBSETS_TOOLTIP_MSG);
    });

    it('Reshuffle subsets should be disabled when training from scratch is not enabled', async () => {
        await renderTrainingConfigParams({
            trainFromScratch: false,
        });

        expect(screen.getByRole('checkbox', { name: /train from scratch/i })).not.toBeChecked();
        expect(screen.getByRole('checkbox', { name: /reshuffle subsets/i })).toBeDisabled();
    });
});
