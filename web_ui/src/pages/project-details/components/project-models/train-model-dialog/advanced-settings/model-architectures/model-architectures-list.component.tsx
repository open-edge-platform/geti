// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Grid, minmax, repeat } from '@geti/ui';

import { PerformanceCategory } from '../../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { RecommendedModelTag } from '../../../models-container/model-card/recommended-model-tag.component';
import { ModelType } from '../../model-types/model-type.component';

interface ModelArchitecturesListProps {
    algorithms: SupportedAlgorithm[];
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateId: string | null;
}

export const ModelArchitecturesList: FC<ModelArchitecturesListProps> = ({
    algorithms,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    activeModelTemplateId,
}) => {
    return (
        <Grid columns={repeat('auto-fit', minmax('size-3000', '1fr'))} gap={'size-250'}>
            {algorithms.map((algorithm) => (
                <ModelType
                    key={algorithm.modelTemplateId}
                    name={algorithm.name}
                    algorithm={algorithm}
                    selectedModelTemplateId={selectedModelTemplateId}
                    onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                    activeModelTemplateId={activeModelTemplateId}
                    renderTag={
                        algorithm.performanceCategory === PerformanceCategory.OTHER
                            ? undefined
                            : () => (
                                  <RecommendedModelTag
                                      performanceCategory={algorithm.performanceCategory}
                                      id={`${algorithm.name.toLocaleLowerCase()}-recommended-tag-id`}
                                  />
                              )
                    }
                />
            ))}
        </Grid>
    );
};
