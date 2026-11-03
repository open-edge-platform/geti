// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { SourceConfig, SourceConfigPayload } from '@/api/types';
import { useTranslation } from '@/i18n';
import { ActionButton, Flex, Loading, Text } from '@geti-ui/ui';
import { Back } from '@geti-ui/ui/icons';
import { usePipeline } from 'hooks/api/pipeline.hook';
import { orderBy } from 'lodash-es';

import { FEATURE_FLAGS } from '../../../constants/feature-flags';
import { useSourcesQuery } from './api/use-sources';
import { EditSourceForm } from './deprecated/edit-source-form.component';
import { SourcesList as DeprecatedSourcesList } from './deprecated/source-list/source-list.component';
import { SourceOptions } from './deprecated/source-options';
import { SourcesList } from './source-list/source-list.component';

export const SourceActions = () => {
    const { t } = useTranslation();
    const [view, setView] = useState<'list' | 'options' | 'edit'>('list');
    const [currentSource, setCurrentSource] = useState<SourceConfig | null>(null);
    const { data: sources = [], isPending } = useSourcesQuery();
    const filteredSources = sources.filter(
        (source): source is SourceConfigPayload => source.source_type !== 'disconnected'
    );
    const existingNames = filteredSources.map((source) => source.name);

    const pipeline = usePipeline();
    const connectedSourceId = pipeline.data.source?.id;

    const handleShowList = () => {
        setView('list');
    };

    const handleAddSource = () => {
        setView('options');
    };

    const handleEditSource = (source: SourceConfig) => {
        setView('edit');
        setCurrentSource(source);
    };

    if (isPending) {
        return <Loading mode={'inline'} size='M' />;
    }

    if (view === 'edit' && currentSource !== null) {
        return (
            <EditSourceForm
                config={currentSource}
                onSaved={handleShowList}
                onBackToList={handleShowList}
                connectedSourceId={connectedSourceId}
            />
        );
    }

    if (view === 'list') {
        const sourcesWithConnectedFirst = orderBy(filteredSources, (source) => source.id === connectedSourceId, 'desc');

        const SourcesListComponent = FEATURE_FLAGS.SOURCES_SINKS_REFACTOR ? SourcesList : DeprecatedSourcesList;

        return (
            <SourcesListComponent
                sources={sourcesWithConnectedFirst}
                onAddSource={handleAddSource}
                onEditSource={handleEditSource}
            />
        );
    }

    return (
        <SourceOptions onSaved={handleShowList} hasHeader={filteredSources.length > 0} existingNames={existingNames}>
            <Flex gap={'size-100'} marginBottom={'size-100'} alignItems={'center'}>
                <ActionButton isQuiet onPress={handleShowList}>
                    <Back />
                </ActionButton>

                <Text>{t('inference.sources.add.title')}</Text>
            </Flex>
        </SourceOptions>
    );
};
