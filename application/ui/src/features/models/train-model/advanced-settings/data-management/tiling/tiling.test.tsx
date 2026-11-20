// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { TrainingConfiguration } from '@/api/types';
import { createI18nInstance } from '@/i18n';
import { fireEvent, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
    getMockedConfigurationParameter,
    getMockedConfigurationParameterGroup,
} from 'mocks/mock-training-configuration';
import { render } from 'test-utils/render';

import { Tiling } from './tiling.component';
import {
    getObjectThresholdParameter,
    getTilingAutomaticDescription,
    getTilingMode,
    getTilingOffDescription,
    getTilingParameters,
    TILING_MODES,
    TilingConfigurableParameterGroup,
    TilingMode,
} from './utils';

describe('getObjectThresholdParameter', () => {
    const threshold = getMockedConfigurationParameter({
        key: 'min_object_ratio_thr',
        value_type: 'float',
        name: 'Object visibility threshold in tile',
        value: 0.5,
        description: "Fraction of an object's bounding box or polygon area that must be visible in a tile",
        default_value: 0.5,
        min_value: 0,
        max_value: 1,
    });

    it('returns the parameter when present', () => {
        const tileSize = getMockedConfigurationParameter({
            key: 'tile_size',
            value_type: 'int',
            name: 'Tile size',
            value: 400,
            description: 'Size of one tile',
            default_value: 400,
        });

        expect(getObjectThresholdParameter([tileSize, threshold])).toBe(threshold);
    });

    it('returns undefined when the backend does not provide it', () => {
        expect(getObjectThresholdParameter([])).toBeUndefined();
    });
});

describe('getTilingMode', () => {
    it('tiling is off when enable tiling parameter is absent', () => {
        expect(getTilingMode([])).toBe(TILING_MODES.OFF);
    });

    it('tiling is off when enable tiling parameter is false', () => {
        expect(
            getTilingMode([
                getMockedConfigurationParameter({
                    key: 'enable',
                    value_type: 'bool',
                    name: 'Enable tiling',
                    value: false,
                    description: 'Whether to apply tiling to the image',
                    default_value: false,
                }),
            ])
        ).toBe(TILING_MODES.OFF);
    });

    it('tiling is automatic when adaptive tiling parameter is true', () => {
        expect(
            getTilingMode([
                getMockedConfigurationParameter({
                    key: 'enable',
                    value_type: 'bool',
                    name: 'Enable tiling',
                    value: true,
                    description: 'Whether to apply tiling to the image',
                    default_value: false,
                }),
                getMockedConfigurationParameter({
                    key: 'enable_adaptive_tiling',
                    value_type: 'bool',
                    name: 'Adaptive tiling',
                    value: true,
                    description: 'Whether to use adaptive tiling based on image content',
                    default_value: false,
                }),
            ])
        ).toBe(TILING_MODES.AUTOMATIC);
    });

    it('tiling is custom when adaptive tiling parameter is false and enable tiling parameter is true', () => {
        expect(
            getTilingMode([
                getMockedConfigurationParameter({
                    key: 'enable',
                    value_type: 'bool',
                    name: 'Enable tiling',
                    value: true,
                    description: 'Whether to apply tiling to the image',
                    default_value: false,
                }),
                getMockedConfigurationParameter({
                    key: 'enable_adaptive_tiling',
                    value_type: 'bool',
                    name: 'Adaptive tiling',
                    value: false,
                    description: 'Whether to use adaptive tiling based on image content',
                    default_value: false,
                }),
            ])
        ).toBe(TILING_MODES.CUSTOM);
    });
});

const getTilingModeButton = (tilingMode: TilingMode) => {
    return screen.getByRole('button', { name: new RegExp(tilingMode, 'i') });
};

describe('Tiling', () => {
    const { t } = createI18nInstance({ lng: 'en' });

    const customParameters = [
        getMockedConfigurationParameter({
            key: 'tile_size',
            value_type: 'int',
            name: 'Tile size',
            value: 256,
            description: 'Size of each tile in pixels',
            default_value: 128,
            max_value: null,
            min_value: 0,
        }),
        getMockedConfigurationParameter({
            key: 'tile_overlap',
            value_type: 'int',
            name: 'Tile overlap',
            value: 64,
            description: 'Overlap between adjacent tiles in pixels',
            default_value: 64,
            max_value: null,
            min_value: 0,
        }),
        getMockedConfigurationParameter({
            key: 'min_object_ratio_thr',
            value_type: 'float',
            name: 'Object visibility threshold in tile',
            value: 0.5,
            description: "Fraction of an object's bounding box or polygon area that must be visible in a tile",
            default_value: 0.5,
            min_value: 0,
            max_value: 1,
        }),
    ];

    const tilingParameters = getMockedConfigurationParameterGroup({
        key: 'tiling',
        name: 'Tiling',
        parameters: [
            getMockedConfigurationParameter({
                key: 'enable',
                value_type: 'bool',
                name: 'Enable tiling',
                value: true,
                description: 'Whether to apply tiling to the image',
                default_value: false,
            }),
            getMockedConfigurationParameter({
                key: 'enable_adaptive_tiling',
                value_type: 'bool',
                name: 'Adaptive tiling',
                value: false,
                description: 'Whether to use adaptive tiling based on image content',
                default_value: false,
            }),
            ...customParameters,
        ],
    }) as TilingConfigurableParameterGroup;

    const App = (props: { tilingParameters: TilingConfigurableParameterGroup }) => {
        const [trainingConfiguration, setTrainingConfiguration] = useState<TrainingConfiguration | undefined>({
            parameters: [
                getMockedConfigurationParameterGroup({
                    key: 'dataset_preparation',
                    parameters: [
                        getMockedConfigurationParameterGroup({
                            key: 'augmentation',
                            parameters: [props.tilingParameters],
                        }),
                    ],
                }),
            ],
        });

        return (
            <Tiling
                tilingParameters={
                    getTilingParameters(trainingConfiguration ?? { parameters: [] }) ?? props.tilingParameters
                }
                onTrainingConfigurationChange={setTrainingConfiguration}
            />
        );
    };

    it('shows the object threshold in automatic mode but not when tiling is off', async () => {
        render(<App tilingParameters={tilingParameters} />);

        fireEvent.click(getTilingModeButton(TILING_MODES.OFF));

        expect(getTilingModeButton(TILING_MODES.OFF)).toHaveAttribute('aria-pressed', 'true');
        expect(getTilingModeButton(TILING_MODES.AUTOMATIC)).toHaveAttribute('aria-pressed', 'false');
        expect(getTilingModeButton(TILING_MODES.CUSTOM)).toHaveAttribute('aria-pressed', 'false');
        expect(screen.getByText(getTilingOffDescription(t))).toBeInTheDocument();
        expect(
            screen.queryByRole('textbox', { name: 'Change Object visibility threshold in tile' })
        ).not.toBeInTheDocument();

        fireEvent.click(getTilingModeButton(TILING_MODES.AUTOMATIC));

        expect(getTilingModeButton(TILING_MODES.AUTOMATIC)).toHaveAttribute('aria-pressed', 'true');
        expect(getTilingModeButton(TILING_MODES.OFF)).toHaveAttribute('aria-pressed', 'false');
        expect(getTilingModeButton(TILING_MODES.CUSTOM)).toHaveAttribute('aria-pressed', 'false');
        expect(screen.getByText(getTilingAutomaticDescription(t))).toBeInTheDocument();
        expect(screen.queryByRole('textbox', { name: 'Change Tile size' })).not.toBeInTheDocument();
        const threshold = screen.getByRole('textbox', { name: 'Change Object visibility threshold in tile' });
        const slider = screen.getByRole('slider', { name: 'Change Object visibility threshold in tile slider' });
        expect(slider).toHaveAttribute('min', '0');
        expect(slider).toHaveAttribute('max', '1');
        expect(threshold).toHaveValue('0.5');
        await userEvent.clear(threshold);
        await userEvent.type(threshold, '0.8');
        await userEvent.tab();
        await userEvent.click(getTilingModeButton(TILING_MODES.CUSTOM));
        expect(screen.getByRole('textbox', { name: 'Change Object visibility threshold in tile' })).toHaveValue('0.8');
        fireEvent.click(getTilingModeButton(TILING_MODES.OFF));
        expect(
            screen.queryByRole('textbox', { name: 'Change Object visibility threshold in tile' })
        ).not.toBeInTheDocument();
        fireEvent.click(getTilingModeButton(TILING_MODES.AUTOMATIC));
        expect(screen.getByRole('textbox', { name: 'Change Object visibility threshold in tile' })).toHaveValue('0.8');
    });

    it('tiling tag updates properly when tiling mode changes', () => {
        render(<App tilingParameters={tilingParameters} />);

        fireEvent.click(getTilingModeButton(TILING_MODES.CUSTOM));

        expect(screen.getByLabelText('Tiling tag')).toHaveTextContent(TILING_MODES.CUSTOM);

        fireEvent.click(getTilingModeButton(TILING_MODES.OFF));

        expect(screen.getByLabelText('Tiling tag')).toHaveTextContent(TILING_MODES.OFF);

        fireEvent.click(getTilingModeButton(TILING_MODES.AUTOMATIC));

        expect(screen.getByLabelText('Tiling tag')).toHaveTextContent(TILING_MODES.AUTOMATIC);
    });

    it('custom tiling parameters updates and resets properly', async () => {
        render(<App tilingParameters={tilingParameters} />);

        fireEvent.click(getTilingModeButton(TILING_MODES.CUSTOM));

        expect(getTilingModeButton(TILING_MODES.CUSTOM)).toHaveAttribute('aria-pressed', 'true');
        expect(getTilingModeButton(TILING_MODES.AUTOMATIC)).toHaveAttribute('aria-pressed', 'false');
        expect(getTilingModeButton(TILING_MODES.OFF)).toHaveAttribute('aria-pressed', 'false');

        for (const parameter of customParameters) {
            const parameterInput = screen.getByRole('textbox', { name: `Change ${parameter.name}` });
            const nextValue =
                parameter.key === 'min_object_ratio_thr' ? '0.8' : (Number(parameter.value) + 1).toString();

            expect(parameterInput).toHaveValue(parameter.value.toString());

            await userEvent.clear(parameterInput);
            await userEvent.type(parameterInput, nextValue);
            expect(parameterInput).toHaveValue(nextValue);

            await userEvent.click(screen.getByRole('button', { name: `Reset ${parameter.name}` }));
            expect(parameterInput).toHaveValue(parameter.default_value.toString());
        }
    });
});
