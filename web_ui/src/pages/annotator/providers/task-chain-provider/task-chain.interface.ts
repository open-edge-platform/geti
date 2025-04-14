// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation, TaskChainInput } from '../../../../core/annotations/annotation.interface';

export interface TaskChainContextProps {
    inputs: ReadonlyArray<TaskChainInput>;
    outputs: ReadonlyArray<Annotation>;
}
