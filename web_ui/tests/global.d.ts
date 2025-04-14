// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface Window {
    FeatureFlags: {
        features: FeaturesFlags;
        enableFeature: (featureFlag: string) => void;
        disableFeature: (featureFlag: string) => void;
    };
}
