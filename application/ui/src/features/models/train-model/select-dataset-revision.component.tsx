// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import { Content, ContextualHelp, Heading, Item, Picker, Section } from '@geti-ui/ui';

import { DatasetSource, useTrainModelState } from './train-model-provider.component';

const SECTION_TITLES: Record<DatasetSource['kind'], string> = {
    current: 'Current dataset',
    view: 'Dataset views',
    revision: 'Dataset revisions',
};

export const SelectDatasetRevision = () => {
    const { t } = useTranslation();
    const { datasetSources, selectedDatasetSourceId, onSelectDatasetSourceId } = useTrainModelState();

    const sections = useMemo(
        () =>
            (['current', 'view', 'revision'] as const)
                .map((kind) => ({
                    id: kind,
                    name: SECTION_TITLES[kind],
                    children: datasetSources.filter((source) => source.kind === kind),
                }))
                .filter(({ children }) => children.length > 0),
        [datasetSources]
    );

    return (
        <Picker
            flex={1}
            items={sections}
	    label={t('models.training.setup.selectDataset.label')}
            data-testid={'select-dataset'}
            selectedKey={selectedDatasetSourceId}
            onSelectionChange={(key) => onSelectDatasetSourceId(String(key))}
            contextualHelp={
                <ContextualHelp variant={'info'} placement={'top'}>
                    <Heading>{t('models.training.setup.selectDataset.helpTitle')}</Heading>
                    <Content>{t('models.training.setup.selectDataset.helpDescription')}</Content>
                </ContextualHelp>
            }
        >
            {(section) => (
                <Section key={section.id} title={section.name} items={section.children}>
                    {(item) => <Item key={item.id}>{item.name}</Item>}
                </Section>
            )}
        </Picker>
    );
};
