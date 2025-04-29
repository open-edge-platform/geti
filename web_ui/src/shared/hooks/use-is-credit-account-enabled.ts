// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';

export const useIsCreditAccountEnabled = () => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    return FEATURE_FLAG_CREDIT_SYSTEM;
};
