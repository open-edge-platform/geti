// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package config

import (
	"media/app/utils"
)

const (
	featureFlagAsynchronousMediaPreprocessing      = "FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING"
	featureFlagDefaultValue                        = false
)

//goland:noinspection GoCommentStart
var (
	FeatureFlagAsynchronousMediaPreprocessing        = utils.GetBoolEnvOrDefault(featureFlagAsynchronousMediaPreprocessing, featureFlagDefaultValue)
)
