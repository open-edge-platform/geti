// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
