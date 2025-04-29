// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { Annotation } from '../../../../core/annotations/annotation.interface';

export interface SaveAnnotationMutation {
    annotations: ReadonlyArray<Annotation>;
    callback?: () => Promise<void>;
}

export type UseSubmitAnnotationsMutationResult = UseMutationResult<void, AxiosError, SaveAnnotationMutation>;
