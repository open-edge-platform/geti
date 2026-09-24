// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Item, Key, Picker } from '@geti-ui/ui';
import { usePatchPipeline } from 'hooks/api/pipeline.hook';
import { useGetActiveModel } from 'hooks/api/use-get-active-model.hook';
import { useGetSuccessfulModels } from 'hooks/api/use-get-models.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty } from 'lodash-es';

import { getAllModelsWithOpenVINOVariants, getModelIdentifierPayload } from '../../../shared/selectable-model';

export const ActiveModel = () => {
    const { t } = useTranslation();
    const { data: models } = useGetSuccessfulModels();
    const activeModel = useGetActiveModel();
    const projectId = useProjectIdentifier();
    const updatePipeline = usePatchPipeline();

    const allModelsWithOpenVinoQuantizedModels = getAllModelsWithOpenVINOVariants(models);

    const handleChange = (key: Key | null) => {
        if (key === null) {
            return;
        }

        const selectedModel = allModelsWithOpenVinoQuantizedModels.find((model) => model.modelVariantId === key);

        if (selectedModel === undefined) {
            return;
        }

        const body = getModelIdentifierPayload(selectedModel);

        updatePipeline.mutate({
            params: { path: { project_id: projectId } },
            body,
        });
    };

    if (isEmpty(allModelsWithOpenVinoQuantizedModels)) {
        return null;
    }

    return (
        <>
            <Picker
                aria-label={'active model'}
                label={t('common.labels.model')}
                labelPosition={'side'}
                items={allModelsWithOpenVinoQuantizedModels}
                onSelectionChange={handleChange}
                selectedKey={activeModel.model_variant_id ?? null}
                minWidth={'size-3400'}
            >
                {(item) => <Item key={item.modelVariantId}>{item.name}</Item>}
            </Picker>
        </>
    );
};
