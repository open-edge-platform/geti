// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key, useState } from 'react';

import { Item, Picker, View } from '@adobe/react-spectrum';
import orderBy from 'lodash/orderBy';

import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { ModelArchitecturesMainContent } from './model-architectures-main-content.component';
import { SortingOptions } from './utils';

type SortingHandler = (templates: SupportedAlgorithm[]) => SupportedAlgorithm[];

const sortingHandlers: Record<SortingOptions, SortingHandler> = {
    [SortingOptions.RELEVANCE]: (templates) => orderBy(templates, 'isDefaultAlgorithm', 'desc'),
    [SortingOptions.SIZE_ASC]: (templates) => orderBy(templates, 'modelSize', 'asc'),
    [SortingOptions.SIZE_DESC]: (templates) => orderBy(templates, 'modelSize', 'desc'),
    [SortingOptions.COMPLEXITY_ASC]: (templates) => orderBy(templates, 'gigaflops', 'asc'),
    [SortingOptions.COMPLEXITY_DESC]: (templates) => orderBy(templates, 'gigaflops', 'desc'),
};

interface SortArchitecturesPickerProps {
    sortBy: SortingOptions;
    onSort: (option: SortingOptions) => void;
}

const SortArchitecturesPicker: FC<SortArchitecturesPickerProps> = ({ sortBy, onSort }) => {
    return (
        <Picker
            isQuiet
            label={'Sort by:'}
            labelAlign={'end'}
            labelPosition={'side'}
            selectedKey={sortBy}
            onSelectionChange={(key: Key) => {
                onSort(key as SortingOptions);
            }}
        >
            <Item key={SortingOptions.RELEVANCE}>Relevance</Item>
            <Item key={SortingOptions.SIZE_ASC}>Size: Small to big</Item>
            <Item key={SortingOptions.SIZE_DESC}>Size: Big to small</Item>
            <Item key={SortingOptions.COMPLEXITY_ASC}>Complexity: Low to high</Item>
            <Item key={SortingOptions.COMPLEXITY_DESC}>Complexity: High to low</Item>
        </Picker>
    );
};

interface ModelArchitecturesProps {
    algorithms: SupportedAlgorithm[];
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateId: string | null;
}

export const ModelArchitectures: FC<ModelArchitecturesProps> = ({
    algorithms,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    activeModelTemplateId,
}) => {
    const [sortBy, setSortBy] = useState<SortingOptions>(SortingOptions.RELEVANCE);
    const sortedAlgorithms = sortingHandlers[sortBy](algorithms);

    return (
        <View>
            <SortArchitecturesPicker onSort={setSortBy} sortBy={sortBy} />
            <ModelArchitecturesMainContent
                algorithms={sortedAlgorithms}
                selectedModelTemplateId={selectedModelTemplateId}
                onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                activeModelTemplateId={activeModelTemplateId}
                sortBy={sortBy}
            />
        </View>
    );
};
