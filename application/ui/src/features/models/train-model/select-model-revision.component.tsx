// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Content, ContextualHelp, Heading, Item, Picker } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { useTrainModelState } from './train-model-provider.component';

export const SelectModelRevision = () => {
    const { t } = useTranslation();
    const { modelRevisions, selectedModelRevisionId, onSelectModelRevisionId } = useTrainModelState();

    return (
        <Picker
            flex={1}
            items={modelRevisions}
            label={t('models.selectInputWeightsLabel')}
            selectedKey={selectedModelRevisionId}
            onSelectionChange={(key) => onSelectModelRevisionId(String(key))}
            contextualHelp={
                <ContextualHelp variant={'info'} placement={'top'}>
                    <Heading>{t('models.selectingInputWeightsHeading')}</Heading>
                    <Content>{t('models.selectModelRevisionHelp')}</Content>
                </ContextualHelp>
            }
        >
            {(item) => <Item key={item.id}>{item.name}</Item>}
        </Picker>
    );
};
