// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { SinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';
import { ActionButton, Flex, Loading, Text } from '@geti-ui/ui';
import { Back } from '@geti-ui/ui/icons';
import { usePipeline } from 'hooks/api/pipeline.hook';
import { isEmpty, orderBy } from 'lodash-es';

import { FEATURE_FLAGS } from '../../../constants/feature-flags';
import { useSinksQuery } from './api/use-sinks-query';
import { EditSinkForm as DeprecatedEditSinkForm } from './deprecated/edit-sink-form.component';
import { SinkList as DeprecatedSinkList } from './deprecated/sink-list/sink-list.component';
import { SinkOptions as DeprecatedSinkOptions } from './deprecated/sink-options';
import { EditSinkForm } from './edit-sink-form.component';
import { SinkList } from './sink-list/sink-list.component';
import { SinkOptions } from './sink-options';
import type { SupportedSinkConfig } from './types';
import { SinkOptions } from './deprecated/sink-options';

const isSupportedSink = (sink: SinkConfig): sink is SupportedSinkConfig => sink.sink_type !== 'ros';

const isSupportedSink = (sink: SinkConfig): sink is SupportedSinkConfig => sink.sink_type !== 'ros';

export const SinkActions = () => {
    const { t } = useTranslation();
    const [view, setView] = useState<'list' | 'options' | 'edit'>('list');
    const [currentSink, setCurrentSink] = useState<SinkConfig | null>(null);
    const { data: sinks = [], isPending } = useSinksQuery();
    const filteredSinks = sinks.filter((sink) => sink.sink_type !== 'disconnected');
    const supportedSinks = filteredSinks.filter(isSupportedSink);

    const pipeline = usePipeline();
    const connectedSinkId = pipeline.data.sink?.id;

    const handleShowList = () => {
        setView('list');
    };

    const handleAddSinks = () => {
        setView('options');
    };

    const handleEditSink = (sink: SinkConfig) => {
        setView('edit');
        setCurrentSink(sink);
    };

    if (isPending) {
        return <Loading mode={'inline'} size='M' />;
    }

    if (view === 'edit' && !isEmpty(currentSink)) {
        if (FEATURE_FLAGS.SOURCES_SINKS_REFACTOR && isSupportedSink(currentSink)) {
            return (
                <EditSinkForm
                    config={currentSink}
                    isConnected={connectedSinkId === currentSink.id}
                    onSaved={handleShowList}
                    onBackToList={handleShowList}
                />
            );
        }

        return (
            <DeprecatedEditSinkForm
                config={currentSink}
                onSaved={handleShowList}
                onBackToList={handleShowList}
                connectedSinkId={connectedSinkId}
            />
        );
    }

    if (view === 'list') {
        if (FEATURE_FLAGS.SOURCES_SINKS_REFACTOR) {
            const supportedSinksConnectedFirst = orderBy(supportedSinks, (sink) => sink.id === connectedSinkId, 'desc');

            return (
                <SinkList sinks={supportedSinksConnectedFirst} onAddSink={handleAddSinks} onEditSink={handleEditSink} />
            );
        }

        const sinksWithConnectedFirst = orderBy(filteredSinks, (sink) => sink.id === connectedSinkId, 'desc');

        return (
            <DeprecatedSinkList
                sinks={sinksWithConnectedFirst}
                onAddSink={handleAddSinks}
                onEditSink={handleEditSink}
            />
        );
    }

    const SinkOptionsComponent = FEATURE_FLAGS.SOURCES_SINKS_REFACTOR ? SinkOptions : DeprecatedSinkOptions;

    return (
        <SinkOptionsComponent onSaved={handleShowList} hasHeader>
            <Flex gap={'size-100'} marginBottom={'size-100'} alignItems={'center'}>
                <ActionButton isQuiet onPress={handleShowList}>
                    <Back />
                </ActionButton>

                <Text>{t('inference.sinks.add.title')}</Text>
            </Flex>
        </SinkOptionsComponent>
    );
};
