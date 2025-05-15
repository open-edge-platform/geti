// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Grid, minmax, repeat } from '@adobe/react-spectrum';
import { capitalize } from 'lodash-es';

import { PerformanceCategory } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { TemplateNameTag } from '../template-name-tag.component';
import { ModelType } from './model-type.component';

interface ModelTypesListProps {
    algorithms: SupportedAlgorithm[];
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateId: string | null;
}

const getBaseAlgorithms = (
    algorithms: SupportedAlgorithm[],
    activeModelTemplateId: string | null
): SupportedAlgorithm[] => {
    const accuracy = algorithms.find((algorithm) => algorithm.performanceCategory === PerformanceCategory.ACCURACY);
    const speed = algorithms.find((algorithm) => algorithm.performanceCategory === PerformanceCategory.SPEED);
    const balance = algorithms.find((algorithm) => algorithm.performanceCategory === PerformanceCategory.BALANCE);

    const baseAlgorithms = [accuracy, speed, balance].filter(Boolean) as SupportedAlgorithm[];

    const activeModelInBaseAlgorithms = baseAlgorithms.find(
        (algorithm) => algorithm.modelTemplateId === activeModelTemplateId
    );

    if (activeModelInBaseAlgorithms === undefined) {
        const activeModelAlgorithm = algorithms.find(
            (algorithm) => algorithm.modelTemplateId === activeModelTemplateId
        );

        if (activeModelAlgorithm !== undefined) {
            baseAlgorithms.push(activeModelAlgorithm);
        }
    }

    return baseAlgorithms;
};

export const ModelTypesList: FC<ModelTypesListProps> = ({
    algorithms,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    activeModelTemplateId,
}) => {
    const baseAlgorithms = getBaseAlgorithms(algorithms, activeModelTemplateId);

    return (
        <Grid columns={repeat('auto-fit', minmax('size-3000', '1fr'))} gap={'size-250'}>
            {baseAlgorithms.map((algorithm) => {
                const isRecommendedAlgorithm = algorithm.performanceCategory !== PerformanceCategory.OTHER;
                const name = isRecommendedAlgorithm ? capitalize(algorithm.performanceCategory) : algorithm.name;

                return (
                    <ModelType
                        name={name}
                        key={algorithm.modelTemplateId}
                        algorithm={algorithm}
                        selectedModelTemplateId={selectedModelTemplateId}
                        onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                        activeModelTemplateId={activeModelTemplateId}
                        renderTag={isRecommendedAlgorithm ? () => <TemplateNameTag name={algorithm.name} /> : undefined}
                    />
                );
            })}
        </Grid>
    );
};
