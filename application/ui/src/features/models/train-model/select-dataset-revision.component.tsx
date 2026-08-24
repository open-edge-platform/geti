// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Content, ContextualHelp, Heading, Item, Picker } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { useTrainModelState } from './train-model-provider.component';

export const SelectDatasetRevision = () => {
    const { t } = useTranslation();
    const { datasetRevisions, selectedDatasetRevisionId, onSelectDatasetRevisionId } = useTrainModelState();

    return (
        <>
            <Picker
                flex={1}
                items={datasetRevisions}
                label={t('models.selectDatasetLabel')}
                selectedKey={selectedDatasetRevisionId}
                onSelectionChange={(key) => onSelectDatasetRevisionId(String(key))}
                contextualHelp={
                    <ContextualHelp variant={'info'} placement={'top'}>
                        <Heading>{t('models.selectingDatasetHeading')}</Heading>
                        <Content>{t('models.selectDatasetRevisionHelp')}</Content>
                    </ContextualHelp>
                }
            >
                {(item) => <Item key={item.id}>{item.name}</Item>}
            </Picker>
        </>
    );
};
