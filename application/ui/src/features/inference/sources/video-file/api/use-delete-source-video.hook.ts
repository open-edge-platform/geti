// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { deleteSourceVideo } from '@/api';
import { useMutation } from '@tanstack/react-query';

export const useDeleteSourceVideo = () => {
    return useMutation({
        mutationFn: (sourceMediaId: string) => deleteSourceVideo(sourceMediaId),
        meta: { error: { notify: () => false } },
    });
};
