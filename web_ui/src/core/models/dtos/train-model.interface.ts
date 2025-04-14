// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersComponentsBodyDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';

export interface TrainingBodyDTO {
    task_id: string;
    model_template_id?: string;
    train_from_scratch: boolean;
    reshuffle_subsets: boolean;
    hyper_parameters?: {
        components: ConfigurableParametersComponentsBodyDTO[];
    };
    max_training_dataset_size?: number;
}
