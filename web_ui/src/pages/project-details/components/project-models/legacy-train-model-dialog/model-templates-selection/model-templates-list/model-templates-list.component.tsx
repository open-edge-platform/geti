// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useState } from 'react';

import { Divider, Grid, Item, Picker, View } from '@geti/ui';
import { isEmpty, orderBy, partition } from 'lodash-es';

import { PerformanceCategory } from '../../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { SliderAnimation } from '../../../../../../../shared/components/slider-animation/slider-animation.component';
import { ModelTemplate } from '../model-template/model-template.component';
import { TrainModelTemplatesProps } from './model-templates-list.interface';

import classes from './model-templates-list.module.scss';

type SortingHandler = (templates: SupportedAlgorithm[]) => SupportedAlgorithm[];

enum SortingOptions {
    RELEVANCE = 'relevance',
    SIZE_DESC = 'size-desc',
    SIZE_ASC = 'size-asc',
    COMPLEXITY_DESC = 'complexity-desc',
    COMPLEXITY_ASC = 'complexity-asc',
}

const sortingHandlers: Record<SortingOptions, SortingHandler> = {
    [SortingOptions.RELEVANCE]: (templates) => orderBy(templates, 'isDefaultAlgorithm', 'desc'),
    [SortingOptions.SIZE_ASC]: (templates) => orderBy(templates, 'modelSize', 'asc'),
    [SortingOptions.SIZE_DESC]: (templates) => orderBy(templates, 'modelSize', 'desc'),
    [SortingOptions.COMPLEXITY_ASC]: (templates) => orderBy(templates, 'gigaflops', 'asc'),
    [SortingOptions.COMPLEXITY_DESC]: (templates) => orderBy(templates, 'gigaflops', 'desc'),
};

interface ModelTemplatesGridProps {
    sortingOption: SortingOptions;
    templates: SupportedAlgorithm[];
    activeModelTemplateIdPerTask: string | undefined;
    selectedModelTemplateId: string;
    handleSelectedTemplateId: (modelTemplateId: string | null) => void;
}

const ModelTemplatesGrid = ({
    sortingOption,
    templates,
    selectedModelTemplateId,
    handleSelectedTemplateId,
    activeModelTemplateIdPerTask,
}: ModelTemplatesGridProps): JSX.Element => {
    const sortingHandler = sortingHandlers[sortingOption];

    return (
        <Grid
            gap={'size-250'}
            marginTop={'size-125'}
            justifyItems={{ base: 'baseline', S: 'center' }}
            columns={['1fr', '1fr']}
        >
            {sortingHandler(templates).map((template: SupportedAlgorithm) => (
                <ModelTemplate
                    key={template.modelTemplateId}
                    template={template}
                    handleSelectedTemplateId={handleSelectedTemplateId}
                    activeModelTemplateIdPerTask={activeModelTemplateIdPerTask}
                    selectedModelTemplateId={selectedModelTemplateId}
                />
            ))}
        </Grid>
    );
};

export const ModelTemplatesList = ({
    templates,
    selectedDomain,
    animationDirection,
    selectedModelTemplateId,
    handleSelectedTemplateId,
    activeModelTemplateIdPerTask,
}: TrainModelTemplatesProps): JSX.Element => {
    const [sortingOption, setSortingOption] = useState<SortingOptions>(SortingOptions.RELEVANCE);
    const [otherTemplates, recommendedTemplates] = partition(templates, [
        'performanceCategory',
        PerformanceCategory.OTHER,
    ]);

    return (
        <View
            id={'model-templates-list-id'}
            padding={'size-175'}
            data-testid={'model-templates-list-id'}
            borderRadius={'regular'}
            maxHeight={{ base: '40vh', M: '50vh' }}
            backgroundColor={'gray-50'}
            overflow={'auto'}
            UNSAFE_className={classes.modelTemplatesBox}
        >
            <Picker
                isQuiet
                label={'Sort by:'}
                labelAlign={'end'}
                labelPosition={'side'}
                selectedKey={sortingOption}
                onSelectionChange={(key: Key) => {
                    setSortingOption(key as SortingOptions);
                }}
            >
                <Item key={SortingOptions.RELEVANCE}>Relevance</Item>
                <Item key={SortingOptions.SIZE_ASC}>Size: Small to big</Item>
                <Item key={SortingOptions.SIZE_DESC}>Size: Big to small</Item>
                <Item key={SortingOptions.COMPLEXITY_ASC}>Complexity: Low to high</Item>
                <Item key={SortingOptions.COMPLEXITY_DESC}>Complexity: High to low</Item>
            </Picker>

            <SliderAnimation animationDirection={animationDirection} key={selectedDomain}>
                {sortingOption === SortingOptions.RELEVANCE ? (
                    <>
                        <ModelTemplatesGrid
                            sortingOption={sortingOption}
                            templates={recommendedTemplates}
                            activeModelTemplateIdPerTask={activeModelTemplateIdPerTask}
                            selectedModelTemplateId={selectedModelTemplateId}
                            handleSelectedTemplateId={handleSelectedTemplateId}
                        />

                        {!isEmpty(otherTemplates) ? (
                            <>
                                <Divider size={'S'} marginY={'size-300'} />
                                <ModelTemplatesGrid
                                    sortingOption={sortingOption}
                                    templates={otherTemplates}
                                    activeModelTemplateIdPerTask={activeModelTemplateIdPerTask}
                                    selectedModelTemplateId={selectedModelTemplateId}
                                    handleSelectedTemplateId={handleSelectedTemplateId}
                                />
                            </>
                        ) : (
                            ''
                        )}
                    </>
                ) : (
                    <>
                        <ModelTemplatesGrid
                            sortingOption={sortingOption}
                            templates={templates}
                            activeModelTemplateIdPerTask={activeModelTemplateIdPerTask}
                            selectedModelTemplateId={selectedModelTemplateId}
                            handleSelectedTemplateId={handleSelectedTemplateId}
                        />
                    </>
                )}
            </SliderAnimation>
        </View>
    );
};
